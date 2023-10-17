import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import chromadb
from autogen.agentchat import UserProxyAgent
from autogen.agentchat.agent import Agent
from autogen.code_utils import extract_code
from autogen.retrieve_utils import (create_vector_db_from_dir,
                                    num_tokens_from_text, query_vector_db)
from IPython import get_ipython

try:
    from termcolor import colored
except ImportError:

    def colored(x, *args, **kwargs):
        return x


PROMPT_DEFAULT = """You're a retrieve augmented chatbot.
User's question is: {input_question}

Context is: {input_context}
"""

PROMPT_CODE = """You're a retrieve augmented coding assistant.
User's question is: {input_question}

Context is: {input_context}
"""

PROMPT_QA = """You're a retrieve augmented chatbot.
User's question is: {input_question}

Context is: {input_context}
"""


class RetrieveUserProxyAgent(UserProxyAgent):
    def __init__(
        self,
        name="RetrieveChatAgent",  # default set to RetrieveChatAgent
        human_input_mode: Optional[str] = "ALWAYS",
        is_termination_msg: Optional[Callable[[Dict], bool]] = None,
        # config for the retrieve agent
        retrieve_config: Optional[Dict] = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            human_input_mode=human_input_mode,
            **kwargs,
        )

        self._retrieve_config = {} if retrieve_config is None else retrieve_config
        self._task = self._retrieve_config.get("task", "default")
        self._client = self._retrieve_config.get("client", chromadb.Client())
        self._docs_path = self._retrieve_config.get("docs_path", None)
        self._collection_name = self._retrieve_config.get(
            "collection_name", "autogen-docs"
        )
        self._model = self._retrieve_config.get("model", "gpt-4")
        self._max_tokens = self.get_max_tokens(self._model)
        self._chunk_token_size = int(
            self._retrieve_config.get(
                "chunk_token_size",
                self._max_tokens * 0.4))
        self._chunk_mode = self._retrieve_config.get(
            "chunk_mode", "multi_lines")
        self._must_break_at_empty_line = self._retrieve_config.get(
            "must_break_at_empty_line", True
        )
        self._embedding_model = self._retrieve_config.get(
            "embedding_model", "all-MiniLM-L6-v2"
        )
        self._embedding_function = self._retrieve_config.get(
            "embedding_function", None)
        self.customized_prompt = self._retrieve_config.get(
            "customized_prompt", None)
        self.customized_answer_prefix = self._retrieve_config.get(
            "customized_answer_prefix", ""
        ).upper()
        self.update_context = self._retrieve_config.get("update_context", True)
        self._get_or_create = (
            self._retrieve_config.get("get_or_create", False)
            if self._docs_path is not None
            else False
        )
        self.custom_token_count_function = self._retrieve_config.get(
            "custom_token_count_function", None
        )
        self._context_max_tokens = self._max_tokens * 0.8
        self._collection = (
            True if self._docs_path is None else False
        )  # whether the collection is created
        self._ipython = get_ipython()
        self._doc_idx = -1  # the index of the current used doc
        self._results = {}  # the results of the current query
        self._intermediate_answers = set()  # the intermediate answers
        self._doc_contents = []  # the contents of the current used doc
        self._doc_ids = []  # the ids of the current used doc
        # update the termination message function
        self._is_termination_msg = (
            self._is_termination_msg_retrievechat
            if is_termination_msg is None
            else is_termination_msg
        )
        self.register_reply(
            Agent,
            RetrieveUserProxyAgent._generate_retrieve_user_reply,
            position=1)

    def _is_termination_msg_retrievechat(self, message):
        if isinstance(message, dict):
            message = message.get("content")
            if message is None:
                return False
        cb = extract_code(message)
        contain_code = False
        for c in cb:
            # todo: support more languages
            if c[0] == "python":
                contain_code = True
                break
        update_context_case1, update_context_case2 = self._check_update_context(
            message)
        return not (
            contain_code or update_context_case1 or update_context_case2)

    @staticmethod
    def get_max_tokens(model="gpt-3.5-turbo"):
        if "32k" in model:
            return 32000
        elif "16k" in model:
            return 16000
        elif "gpt-4" in model:
            return 8000
        else:
            return 4000

    def _reset(self, intermediate=False):
        self._doc_idx = -1  # the index of the current used doc
        self._results = {}  # the results of the current query
        if not intermediate:
            self._intermediate_answers = set()  # the intermediate answers
            self._doc_contents = []  # the contents of the current used doc
            self._doc_ids = []  # the ids of the current used doc

    def _get_context(
            self, results: Dict[str, Union[List[str], List[List[str]]]]):
        doc_contents = ""
        current_tokens = 0
        _doc_idx = self._doc_idx
        _tmp_retrieve_count = 0
        for idx, doc in enumerate(results["documents"][0]):
            if idx <= _doc_idx:
                continue
            if results["ids"][0][idx] in self._doc_ids:
                continue
            _doc_tokens = num_tokens_from_text(
                doc, custom_token_count_function=self.custom_token_count_function)
            if _doc_tokens > self._context_max_tokens:
                func_print = f"Skip doc_id {results['ids'][0][idx]} as it is too long to fit in the context."
                print(colored(func_print, "green"), flush=True)
                self._doc_idx = idx
                continue
            if current_tokens + _doc_tokens > self._context_max_tokens:
                break
            func_print = f"Adding doc_id {results['ids'][0][idx]} to context."
            print(colored(func_print, "green"), flush=True)
            current_tokens += _doc_tokens
            doc_contents += doc + "\n"
            self._doc_idx = idx
            self._doc_ids.append(results["ids"][0][idx])
            self._doc_contents.append(doc)
            _tmp_retrieve_count += 1
            if _tmp_retrieve_count >= self.n_results:
                break
        return doc_contents

    def _generate_message(self, doc_contents, task="default"):
        if not doc_contents:
            print(
                colored(
                    "No more context, will terminate.",
                    "green"),
                flush=True)
            return "TERMINATE"
        if self.customized_prompt:
            message = self.customized_prompt.format(
                input_question=self.problem, input_context=doc_contents
            )
        elif task.upper() == "CODE":
            message = PROMPT_CODE.format(
                input_question=self.problem, input_context=doc_contents
            )
        elif task.upper() == "QA":
            message = PROMPT_QA.format(
                input_question=self.problem, input_context=doc_contents
            )
        elif task.upper() == "DEFAULT":
            message = PROMPT_DEFAULT.format(
                input_question=self.problem, input_context=doc_contents
            )
        else:
            raise NotImplementedError(f"task {task} is not implemented.")
        return message

    def _check_update_context(self, message):
        if isinstance(message, dict):
            message = message.get("content", "")
        update_context_case1 = (
            "UPDATE CONTEXT" in message[-20:].upper()
            or "UPDATE CONTEXT" in message[:20].upper()
        )
        update_context_case2 = (
            self.customized_answer_prefix
            and self.customized_answer_prefix not in message.upper()
        )
        return update_context_case1, update_context_case2

    def _generate_retrieve_user_reply(
        self,
        messages: Optional[List[Dict]] = None,
        sender: Optional[Agent] = None,
        config: Optional[Any] = None,
    ) -> Tuple[bool, Union[str, Dict, None]]:
        if config is None:
            config = self
        if messages is None:
            messages = self._oai_messages[sender]
        message = messages[-1]
        update_context_case1, update_context_case2 = self._check_update_context(
            message)
        if (update_context_case1 or update_context_case2) and self.update_context:
            print(
                colored(
                    "Updating context and resetting conversation.",
                    "green"),
                flush=True,
            )
            # extract the first sentence in the response as the intermediate
            # answer
            _message = message.get("content", "").split("\n")[0].strip()
            _intermediate_info = re.split(r"(?<=[.!?])\s+", _message)
            self._intermediate_answers.add(_intermediate_info[0])

            if update_context_case1:
                # try to get more context from the current retrieved doc results because the results may be too long to fit
                # in the LLM context.
                doc_contents = self._get_context(self._results)

                # Always use self.problem as the query text to retrieve docs, but each time we replace the context with the
                # next similar docs in the retrieved doc results.
                if not doc_contents:
                    for _tmp_retrieve_count in range(1, 5):
                        self._reset(intermediate=True)
                        self.retrieve_docs(
                            self.problem, self.n_results * (2 * _tmp_retrieve_count + 1)
                        )
                        doc_contents = self._get_context(self._results)
                        if doc_contents:
                            break
            elif update_context_case2:
                # Use the current intermediate info as the query text to retrieve docs, and each time we append the top similar
                # docs in the retrieved doc results to the context.
                for _tmp_retrieve_count in range(5):
                    self._reset(intermediate=True)
                    self.retrieve_docs(
                        _intermediate_info[0],
                        self.n_results * (2 * _tmp_retrieve_count + 1),
                    )
                    self._get_context(self._results)
                    doc_contents = "\n".join(
                        self._doc_contents
                    )  # + "\n" + "\n".join(self._intermediate_answers)
                    if doc_contents:
                        break

            self.clear_history()
            sender.clear_history()
            return True, self._generate_message(doc_contents, task=self._task)
        else:
            return False, None

    def retrieve_docs(
            self,
            problem: str,
            n_results: int = 20,
            search_string: str = ""):
        if not self._collection or self._get_or_create:
            print("Trying to create collection.")
            create_vector_db_from_dir(
                dir_path=self._docs_path,
                max_tokens=self._chunk_token_size,
                client=self._client,
                collection_name=self._collection_name,
                chunk_mode=self._chunk_mode,
                must_break_at_empty_line=self._must_break_at_empty_line,
                embedding_model=self._embedding_model,
                get_or_create=self._get_or_create,
                embedding_function=self._embedding_function,
            )
            self._collection = True
            self._get_or_create = False

        results = query_vector_db(
            query_texts=[problem],
            n_results=n_results,
            search_string=search_string,
            client=self._client,
            collection_name=self._collection_name,
            embedding_model=self._embedding_model,
            embedding_function=self._embedding_function,
        )
        self._results = results
        print("doc_ids: ", results["ids"])

    def generate_init_message(
        self, problem: str, n_results: int = 20, search_string: str = ""
    ):
        self._reset()
        self.retrieve_docs(problem, n_results, search_string)
        self.problem = problem
        self.n_results = n_results
        doc_contents = self._get_context(self._results)
        message = self._generate_message(doc_contents, self._task)
        return message

    def run_code(self, code, **kwargs):
        lang = kwargs.get("lang", None)
        if (
            code.startswith("!")
            or code.startswith("pip")
            or lang in ["bash", "shell", "sh"]
        ):
            return (
                0,
                "You MUST NOT install any packages because all the packages needed are already installed.",
                None,
            )
        if self._ipython is None or lang != "python":
            return super().run_code(code, **kwargs)
        else:
            result = self._ipython.run_cell(code)
            log = str(result.result)
            exitcode = 0 if result.success else 1
            if result.error_before_exec is not None:
                log += f"\n{result.error_before_exec}"
                exitcode = 1
            if result.error_in_exec is not None:
                log += f"\n{result.error_in_exec}"
                exitcode = 1
            return exitcode, log, None

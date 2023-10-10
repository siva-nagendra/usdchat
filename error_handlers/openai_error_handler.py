def handle_openai_error(error_code):
    error_mapping = {
        401: {
            "overview": "Invalid Authentication",
            "solution": "Ensure the correct API key and requesting organization are being used.",
        },
        429: {
            "overview": "Rate limit reached for requests",
            "solution": "Pace your requests. Read the Rate limit guide.",
        },
        500: {
            "overview": "The server had an error while processing your request",
            "solution": "Retry your request after a brief wait and contact us if the issue persists. Check the status page.",
        },
        503: {
            "overview": "The engine is currently overloaded, please try again later",
            "solution": "Please retry your requests after a brief wait.",
        },
    }

    error_details = error_mapping.get(
        error_code,
        {"overview": "Unknown Error", "solution": "Please check the documentation."},
    )
    return f"Error ({error_code}): {error_details['overview']}\nSolution: {error_details['solution']}"

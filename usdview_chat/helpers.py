from pxr import Plug


def list_plugins():
    registry = Plug.Registry()
    plugins = registry.GetAllPlugins()
    for plugin in plugins:
        print(plugin.name)


list_plugins()

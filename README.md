<details>
  <summary>ⓘ</summary>

[![Downloads](https://static.pepy.tech/badge/pristan/month)](https://pepy.tech/project/pristan)
[![Downloads](https://static.pepy.tech/badge/pristan)](https://pepy.tech/project/pristan)
[![Coverage Status](https://coveralls.io/repos/github/mutating/transfunctions/badge.svg?branch=main)](https://coveralls.io/github/mutating/pristan?branch=main)
[![Lines of code](https://sloc.xyz/github/mutating/pristan/?category=code)](https://github.com/boyter/scc/)
[![Hits-of-Code](https://hitsofcode.com/github/mutating/pristan?branch=main)](https://hitsofcode.com/github/mutating/pristan/view?branch=main)
[![Test-Package](https://github.com/mutating/pristan/actions/workflows/tests_and_coverage.yml/badge.svg)](https://github.com/mutating/pristan/actions/workflows/tests_and_coverage.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/pristan.svg)](https://pypi.python.org/pypi/pristan)
[![PyPI version](https://badge.fury.io/py/pristan.svg)](https://badge.fury.io/py/pristan)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/mutating/pristan)

</details>

![logo](https://raw.githubusercontent.com/mutating/pristan/develop/docs/assets/logo_1.svg)

This library is designed for creating plugins. What is a plugin? In terms of this library, a plugin is a piece of code that automatically hooks itself into a certain context, into the surrounding code, which knows nothing about the specific plugin. Plugins are a powerful tool for creating easily extensible libraries.

But there are already other plugin libraries! How is this one different? Here are a few key features:

- Maximum simplicity. You simply declare a function and call it in your code. If someone connects their plugin to it, they replace or supplement this function.
- Modern "pythonic" design based on decorators and type annotations.
- Type safety, thread safety, soul safety.


## Table of contents

- [**Installation**](#installation)
- [**Quick start**](#quick-start)
- [**Slots and their defaults**](#slots-and-their-defaults)
- [**Plugins and finding them**](#plugins-and-finding-them)
- [**Type safety**](#type-safety)
- [**Slot as a collection**](#slot-as-a-collection)
- [**Additional restrictions**](#additional-restrictions)


## Installation

Install it:

```bash
pip install pristan
```

You can also quickly try out this and other packages without having to install using [instld](https://github.com/pomponchik/instld).


## Quick start

This library is built on the idea that each plugin automatically finds its slot. What is the slot? It's simple: it's a function with the `@slot` decorator:

```python
from pristan import slot

@slot
def some_slot(a, b) -> dict[str, int]:
    ...
```

How can we add plugins to this function? We use it as a decorator for other functions, like this:

```python
@some_slot.plugin
def plugin_1(a, b) -> int:
    return a + b

@some_slot.plugin
def plugin_2(a, b) -> int:
    return a + b + 1
```

Let's run it:

```python
print(some_slot(1, 2))
#> {'plugin_1': 3, 'plugin_2': 4}
```

Let's pause for a second and reflect on what we've seen. We called a function that we marked as a slot, but in reality the plugins were called, and the result of their call was aggregated into a dictionary. How did the system understand that it needed to combine the result into a dictionary? It did so based on the type annotation. We noted that the slot returns `dict[str, int]`. `dict` here denotes the type of the result container, `str` is the only type of keys denoting plugin names, and the returned values must be of type `int`.

Well, that seems pretty clear, right? But for our functions to become true plugins, they need one more property: **auto-detection**.

Plugins are automatically detected through the entry points mechanism. This is where the magic happens: you can place your plugin functions in a third-party library, add a special entry to `pyproject.toml`, and they will be automatically detected. Here is what such an entry looks like:

```toml
[project.entry-points.pristan]
name = "path.to.plugin.module"
```

That’s basically all you need to create your own libraries and build a plugin infrastructure around them.


## Slots and their defaults

In `pristan`, everything revolves around the concept of slots, so let's take a closer look at what they are.

As already mentioned, a slot is a function to which the `@slot` decorator is applied. However, once you apply this decorator to a function, it is no longer a plain function:

```python
@slot
def some_slot():
    ...

print(some_slot)
#> Slot(some_slot)
```

Yes, we can call it just as we would call the original function, but in fact this is a different object, a wrapper. If this wrapper is called, it will operate according to the following algorithm:

- First of all (on the first call), it will search for plugins.
- If plugins are found: sequentially calls them all, packs the results, and returns it according to the expected type.
- If no plugins are found, it calls the body of the wrapped function, if it is not empty (the body is considered empty if it contains only `...` or `pass`). If it is empty, the slot does nothing. The body of a wrapped function is like a "default plugin" that is called ONLY if there are no real plugins.

When called, the slot returns a value, and the type of this value depends on its return annotation. There are three valid ways to annotate types for slots:

- Missing annotation. In this case, even if the slot calls a certain number of plugins, it will not return anything.
- A list annotation, i.e. `list` or [`typing.List`](https://docs.python.org/3/library/typing.html#typing.List). In this case, the results of each plugin will be collected and returned as a `list`.
- A dictionary annotation, i.e. `dict` or [`typing.Dict`](https://docs.python.org/3/library/typing.html#typing.Dict). The results of each plugin will be collected and returned as a `dict`, where the keys are the names of the plugins and the values are what they returned.

Example:

```python
@slot
def slot_1(a, b) -> dict[str, int]:
    ...

@slot
def slot_2(a, b) -> list[int]:
    ...

@slot
def slot_3(a, b):
    ...

@slot_1.plugin
@slot_2.plugin
@slot_3.plugin
def plugin_1(a, b) -> int:
    return a + b

@slot_1.plugin
@slot_2.plugin
@slot_3.plugin
def plugin_2(a, b) -> int:
    return a + b + 1

print(slot_1(1, 2))
#> {'plugin_1': 3, 'plugin_2': 4}
print(slot_2(1, 2))
#> [3, 4]
print(slot_3(1, 2))
#> None
```

Type annotations are also used to validate return values, as detailed [below](#type-safety).

## Plugins and finding them

In terms of this library, a plugin is a function with the `@<slot_name>.plugin` decorator applied to it.

If the module defining this function has been imported, the plugin has already attached itself to its slot and will be called along with it. But what if the module defining our plugin is never imported or used in the rest of the program? In this case, the plugin will still connect, but to do this, you need to add an entry point pointing to its location to the `pyproject.toml` file (or its equivalent, which also manages entry points, such as `setup.py`). Here is an example of a section in `pyproject.toml` describing the path to the plugin for its automatic installation:

```toml
[project.entry-points.pristan]
name = "path.to.plugin.module"
```

Please note that `path.to.plugin.module` is the path to the module where your plugin is located (in this case, it means that the plugin should be found in the file `path/to/plugin/module.py`), `pristan` is the plugin namespace, and `name` is the name of a specific plugin in this namespace. This plugin name has nothing to do with what you specify in the decorator.

`pristan` is the default plugin namespace, but you can specify a different option for a specific slot, like this:

```python
@slot(entrypoint_group='new_namespace')
def some_slot(a, b):
    ...
```

In this case, the entry in `pyproject.toml` should look like this:

```toml
[project.entry-points.new_namespace]
name = "path.to.plugin.module"
```

I recommend that large libraries use namespaces that correspond to their names.


## Type safety

This library provides type safety in two aspects:

- All plugins are checked for compatibility between their signatures and the slot signature.
- If the slot has a type annotation, the return type of each plugin is automatically checked.

This ensures that slots and plugins can be easily integrated into the surrounding code: plugins can be called in the expected manner and return values of the required types. Let's take a closer look at these checks.

**First, we check the signatures**. How does it work? Before anything else, you should know that Python syntax is very flexible. Often, the same argument can be passed to a function both by position and by name. That's why you can't just compare signatures for equality; you need a smarter approach. You shouldn't compare the signatures themselves, but rather *how the functions are actually called*.

By default, the `pristan` library expects that there is at least one common valid calling convention between the slot and each of its plugins. If this does not exist, you will immediately get an exception when trying to connect such a plugin:

```python
@slot
def some_slot():
    ...

@some_slot.plugin
def plugin(a, b):
    return a + b + 1

#> ...
#> sigmatch.errors.SignatureMismatchError: No common calling method has been found between the slot and the plugin.
```

This approach allows you to eliminate the most serious signature errors. However, it does not take into account *how the slot will actually be called*, which means that incompatibility errors between the slot and the plugin can still occur at the call stage. If you want to completely protect yourself from such errors, you need to pass a description of the expected call pattern when creating a slot, using the special syntax of the [`sigmatch`](https://github.com/mutating/sigmatch) library:

```python
@slot(signature="..")  # This description means that parameters will be passed to the function only by position and in no other way.
def some_slot(a, b):
    ...
```

In this case, even functions that in principle share a common calling convention with the slot but do not match the expected one will be filtered out:

```python
@some_slot.plugin
def plugin(a, *, b):  # The asterisk indicates that argument b can only be passed by name, whereas the expected signature explicitly prohibits this.
    return a + b + 1

#> ...
#> sigmatch.errors.SignatureMismatchError: The signature of the callable object does not match the expected one.
```

**Second, we check the return values**. It seems like everything should be simpler here, right? Well, let's see.

The type of the expected plugin value is determined by the slot’s return annotation. The following annotations imply no type checks for plugins at all:

```python
@slot
def slot_1():
    ...

@slot
def slot_2() -> list:
    ...

@slot
def slot_3() -> dict:
    ...
```


With an empty annotation, everything is clear. `list` and `dict` annotations describe only how values are aggregated, not their types. However, a more precise slot annotation will be used to verify the values returned by plugins:

```python
@slot
def slot_1() -> list[int]:
    ...

@slot
def slot_2() -> dict[str, int]:
    ...

@slot_1.plugin
@slot_2.plugin
def plugin():
    return 'some string'

slot_1()
#> ...
#> TypeError: The type str of the plugin's "plugin" return value 'some string' does not match the expected type int.
slot_2()
#> ...
#> TypeError: The type str of the plugin's "plugin" return value 'some string' does not match the expected type int.
```

I recommend specifying annotations for slots that are as strict as possible. However, [`simtypes`](https://github.com/mutating/simtypes), a very simple library, is used as the type checker under the hood. It does not support most of the special annotations from [`typing`](https://docs.python.org/3/library/typing.html). Your annotations should be as literal as possible, i.e., directly describing the types of values you expect (although some additional typing features are also supported, such as `Union` or `Any`).


## Slot as a collection

You can treat a slot as a collection of plugins.

Each slot and each plugin in it has a name. By default, the name of the slot or plugin is the name of the function the corresponding decorator is applied to:

```python
@slot
def some_slot():  # <- Here, the name of the slot is just "some_slot".
    ...

@some_slot.plugin
def plugin_name():  # <- And here, the name of the plugin is just "plugin_name".
    ...
```

You can change these names by passing the desired values as the first positional argument:

```python
@slot('some_another_slot_name')  # <- Look! Here, the name of the slot is "some_another_slot_name".
def some_slot():
    ...

@some_slot.plugin('another_plugin_name')  # <- The plugin name is "another_plugin_name".
def plugin_name():
    ...
```

The plugin name must be a valid Python identifier. However, if more than one plugin with the same name is attached to a single slot, the system will automatically change their names to remain unique by appending a number to the end, starting with the second plugin (`plugin_name`, `plugin_name-2`, and so on).

Now that we know what plugin names are, let's look at basic operations with the slot as a collection.

Get a list of names of installed plugins:

```python
@slot
def some_slot():
    print('run the slot default function')

@some_slot.plugin('name')
def plugin_1():
    print('run the "plugin_1" function')

@some_slot.plugin('name')
def plugin_2():
    print('run the "plugin_2" function')

@some_slot.plugin('name2')
def plugin_3():
    print('run the "plugin_3" function')

print(some_slot.keys())
#> ('name', 'name2')
```

Note that you only get the base (declared) names, without the numeric suffixes that are added when names are duplicated! This minimizes how much your other code needs to know about the set of installed plugins.

You can also use names to check for the presence of certain plugins:

```python
print('name' in some_slot)
#> True
print('name-2' in some_slot)
#> True
print('name-3' in some_slot)
#> False
```

Plugins can be requested using their names as keys:

```python
some_slot['name']
```

You can use either the base plugin name or the name with the numeric suffix. In the first case, you may get multiple plugins; in the second case, at most one. The return value is a callable object! If you call it, all plugins in the selection will be called. However, if the selection is empty, the default slot function will be called when the object is called. In short, you can treat the returned object as a slot with all plugins that do not match the search criteria removed:

```python
some_slot['name']()
#> run the "plugin_1" function
#> run the "plugin_2" function

some_slot['non_existent_key']()
#> run the slot default function
```

You can use the [`len()`](https://docs.python.org/3/library/functions.html#len) function to find out how many plugins you have:

```python
print(len(some_slot))
#> 3
print(len(some_slot['name']))
#> 2
```


## Additional restrictions

You can impose some additional restrictions on slots or individual plugins.

The simplest restriction at the slot level is the number of plugins that can be installed to it. To set it, pass the `max` argument to the decorator:

```python
@slot(max=1)
def some_slot():
    ...

@some_slot.plugin
def plugin_1():
    ...

@some_slot.plugin
def plugin_2():
    ...

#> ...
#> pristan.errors.TooManyPluginsError: The maximum number of plugins for this slot is 1.
```

You can also restrict a plugin to a specific version of the library that declares the slot. To do this, pass a version expression as the `engine` argument:

```python
@slot
def some_slot():
    ...

@some_slot.plugin(engine='>1.0.0')
def plugin():
    ...
```

> ⓘ A version expression is one of five comparison operators (`>`, `<`, `==`, `>=`, `<=`) + the library version to compare against.

If the library version check fails, the plugin will not be installed in the slot.

A plugin may also require its name to be unique within the slot. To do this, pass `unique=True` to the plugin decorator:

```python
@some_slot.plugin(unique=True)
def plugin():
    ...

@some_slot.plugin
def plugin():
    ...

#> ...
#> pristan.errors.PrimadonnaPluginError: Plugin "plugin" claims to be unique, but there are other plugins with the same name.
```

These are all the restrictions that can be configured for now.

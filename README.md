![logo](https://raw.githubusercontent.com/pomponchik/pristan/develop/docs/assets/logo_1.svg)

This is a library designed for creating plugins. What is a plugin? In terms of this library, a plugin is a piece of code that automatically “pulls itself” into a certain context, into the surrounding code, which knows nothing about the specific plugin. Plugins are a powerful tool for creating powerful and easily extensible libraries.

But there are already other plugin libraries! How is this one different? Here are a few things:

- Maximum simplicity. You simply declare a function and call it in your code. If someone connects their plugin to it, they simply replace or supplement this function.
- Modern "pythonic" design based on decorators and type annotations.
- Type safety, thread safety, safety of your soul.


## Table of contents

- [**Installation**](#installation)
- [**Quick start**](#quick-start)


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

How can we add a plugin to this function? We need to use it as a decorator for other functions, like this:


```python
@some_slot.plugin('plugin_name')
def plugin_1(a, b) -> int:
    return a + b

@some_slot.plugin('plugin_name_2')
def plugin_2(a, b) -> int:
    return a + b + 1
```

Let's try to start it up?

```python
print(some_slot(1, 2))
#> {'plugin_name': 3, 'plugin_name_2': 4}
```

Let's pause for a second and reflect on what we've seen. We called a function that we marked as a slot. But in reality, plugins were called, and the result of their call was aggregated into a dictionary. How did the system understand that it needed to combine the result into a dictionary? It did so based on the type annotation.

We noted that the slot returns `dict[str, int]`. `dict` here denotes the type of the result container, `str` is the only type of keys denoting plugin names, and the returned values must be of type `int`.

Well, that seems pretty clear, right? But for our functions to become true plugins, they lack one more property: **auto-detection**.

Plugins are automatically detected through the entry points mechanism. This is where the magic happens: you can place your plugin functions in a third-party library, add a special mark to `pyproject.toml`, and they will be automatically detected. Here is what such a mark looks like:

```toml
[project.entry-points.pristan]
name = "path.to.plugin.module"
```

That's really all you need to know to create your own libraries and the entire plugin infrastructure around them. But if you're interested in the details, read on.







## Требования

- Архитектура: слот-плагин. Базовая библиотека задает "слот": специальный объект, определяющий формат плагина и осуществляющий его поиск. Библиотека с плагином импортирует слот и регистрируется в нем.
- Поддержка плагинов-компаньонов с возможностью указать требуемую библиотеку и опционально ее версию (либо несколько библиотек)

Слот определяет следующее:

- Ожидается один плагин или больше
- Плагин "по умолчанию", который не используется, если определен хотя бы один другой
- Ожидается ли от плагина наличие ключа (ключ и имя плагина - разные вещи, ключ используется при поиске, а имя плагина - при отображении)
- Характер 

Плагин характеризуется:

- Именем
- Ожидающим его слотом
- Опционально: слот (если слот того требует)

## Что такое плагин

Плагин - это произвольная функция, принимающая аргументы, формат которых задан слотом

## Что такое слот

- Произвольная функция, обернутая спец декоратором @slot
- Декоратор может быть с аргументами и без
- Возможные аргументы: обязательность ключа (по умолчанию не обязателен), список экранируемых исключений
- По умолчанию от плагина ожидается сигнатура, идентичная слоту
- Можно задать произвольную сигнатуру (в этом случае сам слот проверяется на соответствие сигнатуре)
- Если у слота заданы типы аргументов, а также возвращаемых значений, они проверяются при вызове плагинов
- Если у слота есть непустое тело (считается пустым, если там pass или Ellipsis), это считается плагином по умолчания
- По умолчанию не экранирует исключения внутри плагинов, но может, если передать, что 
- Сохраняет или нет результаты вызова плагинов в зависимости от тайп-хинта
- Поддерживает докстринги (они не влияют на оценку "заполненности" слота)
- Если задать тело, но не задать тайп-хинт возвращаемого значения - будет исключение
- При попытке задать 2 разным плагинам 1 имя - исключение
- Если задать любой хинт возвращаемого значения, кроме `list[...]`, `list`, `List`, `List[...]`, `<ничего>`, `Dict[..., ...]`, `Dict`, `dict[..., ...]`, `dict` - исключение
- Задать хинт возвращаемого значения как дикт можно только если ключи обязательны, иначе - исключение
- Если слот требует ключи, и сам определяет возвращаемое значение, у него должен быть задан ключ, иначе - исключение
- Если хинт возвращаемого задан как дикт, агрегируем по ключам в словарь
- сли хинт возвращаемого задан как лист, агрегируем по порядку в лист
- Слот присваивает каждому плагину имя. По умолчанию это имя, запрошенное плагином, иначе - запрошенное имя + номер (если такое имя запросили несколько плагинов)

В последующих релизах можно добавить:

- Таймаут на вызов 1 плагина или всех (возможна реализация через токены отмены)


## Что такое плагин

Плагин - это функция с декоратором `@slot_object.plugin`



Умеет проверять совместимость с движком




## Примеры синтаксиса

Определения слота:

```python
from pristan import slot


# Простейший слот на два аргумента, результаты вызова плагинов никак не сохраняются, типы входов и выходов никак не проверяются, возвращаемые значения не агрегируются (возвращается None)
# Телом также может быть pass
@slot
def some_slot_1(a, b):
    ...

# Слот с проверкой типов на входе и выходе, содержимое самого слота будет вызвано только если не задан ни один плагин, результаты агрегируются
@slot
def some_slot_2(a: int, b: str) -> list[str]:
    return [f'{a}: {b}']


# Слот с проверкой типов только на входе и выходе, результат не агрегируется
@slot
def some_slot_3(a: int, b: str):
    return [f'{a}: {b}']


# Невозможно зарегистрировать плагин без ключа
# 
@slot(keys_required=True, key='some_key')
def some_slot_4(a: int, b: str) -> list[str]:
    return [f'{a}: {b}']


# Экранируем в при вызове плагинов перечисленные исключения
# Еще возможные варианты: ... (базовые ислючения модуля escaping), [ValueError, KeyError] (два разных исключения), [ValueError, KeyError, ...] (два исключения + все базовые)
@slot(escape: ValueError)
def some_slot_5(a: int, b: str) -> list[str]:
    return [f'{a}: {b}']

# Ожидается строго 1 плагин
@slot(how_many=1)
def some_slot_6(a: int, b: str) -> list[str]:
    return [f'{a}: {b}']


# Ожидается больше 1 плагина
@slot(how_many='>1')
def some_slot_7(a: int, b: str) -> list[str]:
    return [f'{a}: {b}']


# Под капотом используется либа sigmatch для сверки сигнатуры
@slot(signature=['a', 'b'])
def some_slot_8(a: int, b: str, c=5) -> list[str]:
    return [f'{a}: {b}']
    

# По дефолту ищется entry point "имя библиотеки, где объявлен слот (если есть) + _ + имя функции-слота"
@slot(entry_point='lol_kek')
def some_slot_9(a: int, b: str) -> list[str]:
    return [f'{a}: {b}']


# Определяем минимальную версию базовой библиотеки (движка, куда подключаются плагины)
@slot(engine='>=1.0.0')
def some_slot_10(a: int, b: str) -> list[str]:
    return [f'{a}: {b}']
```

Определение плагина:

```python
# Файл находится внутри библиотеки, которая будет найдена по entry_point
from module_with_slots import some_slot_1

@some_slot_1.plugin('plugin_name')
def some_plugin(a: int, b: str) -> str:
    return 'kek'
```

Использование слота:

```python
from module_with_slots import some_slot_1


results = some_slot_3(1, 'kek') # вызов с агрегацией
#> ['lol', 'kek']

# слот - словаре-подобный объект
# значение возвращается вне зависимости от того, агрегируется значение слотом или нет
result = some_slot_3['key'](1, 'kek')
```

## Как реализовать поверх плагина сбор мутаций

- Упаковываем плагин внутрь объекта класса Х
- Коллектим мутации, каждую с уникальным именем
- Запускаем мутации внутри плагина


## Пока думаю

- Как передавать в плагин мету? Например, присвоенное ему слотом имя
- Собирать статистику?


Слот с `return []` (для аннотаций с листом) и `return {}` (для аннотаций с диктом) считается пустым

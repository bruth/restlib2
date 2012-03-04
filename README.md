Django RESTlib: HTTP for Programmers
====================================
Inspired by [Requests][1], RESTlib2 is an HTTP library which simplifies
creating dynamic Web resources in Python. RESTlib2 focuses on embracing
HTTP and enables clean transparent implementations of your resources.

Why?
----
Web frameworks typically layer on the abstractions for handling
the request/response process. These abstractions decrease implementation
transparency and results in fragmented modifications of your response
object.

[Django][2], for example, is a full stack Web framework which has a
[middleware layer][3] that enables processing and/or augmenting the request
and response objects before and after the _view_ (called a controller in
MVC stacks) processes the request. Along with the middleware, there are
[numerous][4] [decorators][5] which can be used to wrapped the view to
modify the process the request headers or modify the response headers.

Django is not at fault here. It was not designed to provide a REST API
with the notion of a _resource_. It's background and intent is
to make it trivial to stand up websites and the core developers (and
the community) take an extremely pragmatic approach to achieve this.

Aside from Django core, [django-tastypie][6] is the most popular app that
provides an API for defining resources in Django. Unfortunately, tastypie
has too complicated of an API and too many abstractions to understand
how it works. The developer must work within the confines of this intricate
and arbitrary API, rather than embracing and confidently working with
the inferred _API_ HTTP provides.

RESTlib2 intends to provide a more simple, natural and familiar API for
creating dynamic Web resources in Python.

[1]: http://python-requests.org
[2]: http://www.djangoproject.com
[3]: https://docs.djangoproject.com/en/1.3/ref/middleware/
[4]: https://docs.djangoproject.com/en/1.3/topics/conditional-view-processing/
[5]: https://docs.djangoproject.com/en/1.3/topics/http/decorators/
[6]: http://django-tastypie.readthedocs.org/en/latest/index.html

Features
--------
* Familiar API for defining resources using common HTTP terminology
* Simple API for fully embedding resources or referencing resources by
  their own endpoint (see [HATEOAS][7])
* Resource methods (e.g. `get`, `put`, `post`) have access to both the
  `request` and `response` objects. Augment the response object as needed.
* Support for defining versions of a resource in the `Content-Type`, e.g.
  `application/json, version=1`
* Abstract `Resource` class for quick integration with your favorite
  Web framework
* Built-in implementions for common Web frameworks including Django,
  and Werkzeug

[7]: http://en.wikipedia.org/wiki/HATEOAS

Examples
--------

**Barebone Example** (no sugar)

```python
import json

class Author(Resource):
    supported_accept_types = ['application/json']

    def get(self, request, response):
        return json.dumps([{
            'first_name': 'John',
            'last_name': 'Doe',
            'birth_date': '1954-03-29',
        }, {
            'first_name': 'Jane',
            'last_name': 'Doh',
            'birth_date': '1958-01-13',
        }])
```

* ``supported_accept_types`` defines the supported encoding types and rejects
  requests only does not accept `application/json`
* Since the `get` method is only defined, `post`, `put`, `patch`, and
  `delete` are not allowed for this resource. `head` is accessible if
  `get` is defined and `options` is always available unless the service
  is set as unavailable

Composite Resources
------------------
When designing a REST API, an important decision to make up front is
whether a _chatty_ service is preferred, or a service that requires
more bandwith per request.

The latter of the two is a result of embedding resources in other related
resources. For example, the first response entity below simply has a
reference to the endpoint where author `id` is available. Thus in order to
get the data about the author, a second request is required.

The second response entity has the author data embedded in the book data.
This will require more bandwith, but will not require subsequent requests.

```javascript
// Referenced
{
    "title": "Learn Python The Hard Way",
    "publish_date": "2010-05-01",
    "author": {
        "id": 1,
        "url": "http://example.com/author/1"
    }
}

// Embedded
{
    "id": 1,
    "title": "Learn Python The Hard Way",
    "publish_date": "2010-05-01",
    "author": {
        "id": 1,
        "first_name": "Zed",
        "last_name": "Shaw"
        // ...
    }
}
```

Deciding whether to embed data in another entity can be answered with a
simple question:

> Is it likely the two entities are represented together in client
applications?

Note that embedding resources does not preclude resources from having their
own endpoints (as in the first example).

For a large collection of objects, choosing to not embed related resources
results in the client needing to potentially make hundreds or thousands
additional requests.

RESTlib2 provides an API for reusing resources by either referencing them
(first example) or embedding them directly (second example).

```python
>>> book = Book()
>>> book.apply_get()
[{ ... }, ...]
>>> book.apply_get(pk=1)
{ ... }
```

Philosophy
----------

* **Be pragmatic.** Don't attempt to solve the world's problems in a single
  resource. Each should be written with equal purpose in mind.
* **Keep it simple.** Don't concern yourself with the details until you
  absolutely need to. Setting a plethora of headers will only make things
  more complicated.
* **Be consistent.** If you make use of HATEOAS (and you should), use it
  everywhere it makes sense. Support the same mimetypes across your service.
* **Keep it visible.** Resources should be as _visible_ as possible. Do not
  obfuscate or overcomplicate how a request is handled, otherwise processing
  becomes non-deterministic.

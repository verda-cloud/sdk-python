Following redirects inside a deployment
=======================================

By default, ``InferenceClient`` does not follow HTTP redirects. A 3xx response raises ``InferenceClientError``, and the error message shows the ``Location`` value.

Set ``follow_redirects=True`` if your container sends redirects inside its own deployment. The client then follows a redirect only if all of these are true:

- The target has the same scheme, host and port as ``endpoint_base_url``.
- The target path is the deployment path, or it starts with the deployment path and ``/``.
- The target path passes the same check as ``path``.
- The client followed fewer than 5 redirects.

The client raises ``InferenceClientError`` for any other redirect. ``AsyncInferenceExecution.status_json()`` and ``result()`` never follow a redirect.

``Deployment.run_sync`` and ``Deployment.run`` always use the default. To follow redirects, create an ``InferenceClient`` with the deployment's ``endpoint_base_url``, as this example shows.

.. literalinclude:: ../../../../examples/containers/calling_the_endpoint_with_redirects.py
   :language: python
   :caption: Following redirects inside a deployment

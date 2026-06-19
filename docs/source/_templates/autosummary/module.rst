{{ fullname }}
{{ "=" * fullname|length }}

.. currentmodule:: {{ fullname }}

Summary
-------

{% if classes %}
Classes
~~~~~~~

{% for item in classes %}
* :class:`{{ item }}`
{% endfor %}
{% endif %}

{% if functions %}
Functions
~~~~~~~~~

{% for item in functions %}
* :func:`{{ item }}`
{% endfor %}
{% endif %}

Details
-------

.. automodule:: {{ fullname }}
   :members:
   :undoc-members:
   :show-inheritance:

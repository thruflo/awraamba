<%inherit file="base.mako"/>

<%def name="sub_title()">${_("Error")}</%def>

<h1>${_(title)}</h1>
<p class="error message">
  ${_(error)}
</p>
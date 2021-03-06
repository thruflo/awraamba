<%inherit file="base.mako"/>
<%namespace name="macros" file="macros.mako"/>

<%def name="sub_title()">${_(u'Signup')}</%def>

<div class="content">
  <div class="page-header">
    <h1>${_(u'Signup')} <small>${_(u'join the %(site_title)s!' % settings)}</small></h1>
  </div>
  <div class="row">
    <div class="span10">
      <h2>${_(u'Create your account')}</h2>
      ${macros.form(
          attrs = dict(action='/signup', method='post'),
          fields = (
              ('text_input', 'username'),
              ('text_input', 'email'),
              ('password_input', 'password'),
              ('password_input', 'confirm'),
          ),
          actions = (
              ('submit_action', _(u'Signup')),
          )
      )}
    </div>
    <div class="span4">
      <!-- h3 /-->
    </div>
  </div>
</div>

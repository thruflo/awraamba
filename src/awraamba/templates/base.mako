<%def name="sub_title()"></%def>
<%def name="sub_headers()"></%def>
<!DOCTYPE HTML>
<html lang="${localizer.locale_name}">
  <head>
    <meta charset="utf-8" />
    <title>${request.registry.settings['site_title']} / ${self.sub_title()}</title>
    % if not is_ajax:
      <meta name="description" content="${_(u'%(site_title)s ...' % request.registry.settings)}" />
      <meta name="keywords" content="${_(u'Awra,Amba,AwraAmba,...')}" />
      <meta name="author" content="Write This Down Productions Ltd., Julie Kim, James Arthur." />
      <meta http-equiv="Content-Language" content="${localizer.locale_name}" />
      <!--[if lt IE 9]>
        <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
      <![endif]-->
      <link rel="shortcut icon" href="/favicon.ico" />
      <link type="text/css" rel="stylesheet"
          href="${request.static_url('awraamba:assets/base.css')}"
      />
      <link type="text/css" rel="stylesheet"
          href="${request.static_url('awraamba:assets/style.css')}"
      />
      ${self.sub_headers()}
    % endif
  </head>
  <body>
    <div class="topbar">
      <div class="topbar-inner">
        <div class="container-fluid">
          <a class="brand" href="/">${request.registry.settings['site_title']}</a>
          <ul class="nav">
            <li class="active"><a href="/">Themes</a></li>
            <li><a href="/about">Characters</a></li>
            <li><a href="/contact">Locations</a></li>
          </ul>
          % if not current_user:
            <form action="/signup" method="get" class="pull-right">
              &nbsp;
              <button class="btn primary" type="submit">${_(u'Signup')}</button>
            </form>
            <form action="/login" method="post" class="pull-right">
              <input type="hidden" name="csrf_token" value="${request.session.get_csrf_token()}" />
              <input class="input-small" type="text" placeholder="${_(u'Username')}" />
              <input class="input-small" type="password" placeholder="${_(u'Password')}">
              <button class="btn" type="submit">${_(u'Login')}</button>
            </form>
          % else:
            <ul class="nav secondary-nav">
              <li class="dropdown">
                <a class="dropdown-toggle" href="#">${current_user.username}</a>
                <ul class="dropdown-menu">
                  <li><a href="/users/${current_user.username}">${_(u'Profile')}</a></li>
                  <li class="disabled"><a href="/users/${current_user.username}/request.registry.settings">${_(u'request.registry.settings')}</a></li>
                  <li class="divider"></li>
                  <li><a href="/logout">${_(u'Logout')}</a></li>
                </ul>
              </li>
            </ul>
          % endif
        </div>
      </div>
    </div>
    <div id="main-content" class="container-fluid">
      ${next.body()}
      <footer>
        <p>&copy; 2011 Write This Down Productions Ltd.</p>
      </footer>
    </div>
    % if not is_ajax:
      <script type="text/javascript" src="//ajax.googleapis.com/ajax/libs/jquery/1.6.4/jquery.min.js">
      </script>
      <script type="text/javascript" src="/client_strings.json">
      </script>
      <script type="text/javascript" src="${request.static_url('awraamba:assets/base.js')}">
      </script>
      <script type="text/javascript" src="${request.static_url('awraamba:assets/client.js')}">
      </script>
      <script type="text/javascript" src="${request.static_url('awraamba:tour/tour.js')}">
      </script>
      <!--script type="text/javascript">
        var _gaq = _gaq || [];
        _gaq.push(['_setAccount', '${request.registry.settings["google_analytics"]}']);
        _gaq.push(['_setDomainName', '${request.host}']);
        _gaq.push(['_trackPageview']);
        (function() {
          var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
          ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
          var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
        })();
      </script-->
    % endif
  </body>
</html>
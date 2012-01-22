# Provides the client application `Controller` and the `main()` entry point.
define 'app', (exports, root) ->
  
  # `BaseController` implements the machinery to change between views.
  class BaseController extends Backbone.Router
    # View show / hide machinery.
    _views: {}
    _current_view: null
    _create_view: (view_name) ->
      # By convention, `@_show 'foo_view` instantiates a `views.FooView`
      # with `$('#foo-view') as its element and an empty model instance`.
      parts = (s.toTitleCase() for s in view_name.split('_'))
      ViewClass = views["#{parts.join ''}"]
      el = $ "##{view_name.replace('_', '-')}"
      model = new Backbone.Model
      new ViewClass el: el, model: model
    
    _get_or_create: (view_name) ->
      console.log 'BaseController._get_or_create'
      if not (view_name of @_views)
        console.log 'Does not exist', view_name
        @_views[view_name] = @_create_view view_name
      @_views[view_name]
    
    _show_current: ->
      # Fade the current view in.
      @_current_view.trigger 'beforeshow'
      $target = @_current_view.$el
      $target.css opacity: 0.1
      @_current_view.trigger 'show'
      $target.animate opacity: 1, 1500, =>
        @_current_view.trigger 'aftershow'
    
    _show: (view_name, callback) ->
      # If it's the first time the user has visited, show the intro page.
      if awraamba.template_variables.is_first_time
        awraamba.template_variables.is_first_time = false
        if view_name isnt 'intro_view'
          view = @_get_or_create 'intro_view'
          view.model.set 'value', window.location.pathname
          return @navigate '/intro', true
      # Else fade the previous view out and the next view in.
      previous_view = @_current_view
      @_current_view = @_get_or_create view_name
      if previous_view?
        previous_view.trigger 'beforehide'
        $target = $ previous_view.el
        $target.animate opacity: 0.1, 1500, =>
          previous_view.trigger 'hide'
          previous_view.trigger 'afterhide'
          @_show_current()
      else
        @_show_current()
      callback @_current_view if callback?
    
    # Patch `Backbone.Router.navigate` to allow us to use absolute paths when
    # writing hrefs, e.g.: `<a href="/foo/bar">` whilst still supporting paths
    # from location state changes, which come through `Backbone.checkURL()`.
    navigate: (path, trigger_route) =>
      # Normalise the path by stripping any leading `/` from it.
      path = path.slice(1) if path.charAt(0) is '/'
      super path, trigger_route
    
  
  # `Controller` exposes the application specific routes.
  class Controller extends BaseController
    # Map url paths to method names.
    routes:
      ''                              : 'explore'
      'intro'                         : 'intro'
      'explore'                       : 'explore'
      'explore/:location'             : 'explore'
      'themes'                        : 'watch'
      'themes/:theme'                 : 'theme'
      'scarf'                         : 'interact'
      'scarf/:reaction'               : 'interact'
      ':user'                         : 'profile'
    # Handler methods.
    intro: =>
      console.log 'Controller.intro'
      @_show 'intro_view'
    
    explore: (location) =>
      console.log "Controller.explore #{location}"
      @_show 'explore_view', (view) => view.model.set 'value', location
    
    watch: =>
      console.log "Controller.watch"
      @_show 'watch_view'
    
    theme: (theme) =>
      console.log "Controller.theme #{theme}"
      @_show 'theme_view', (view) => view.model.set 'value', theme
    
    interact: (reaction) =>
      console.log "Controller.interact #{reaction}"
      @_show 'interact_view', (view) => view.model.set 'value', reaction
    
  
  # `main()` application entry point.  Call it to start the javascript.
  exports.main = ->
    # Prevent clickjacking.
    if self isnt top
      top.location = self.location
      return
    # Initialise the controller and provide `app.navigate`.
    controller = new Controller
    exports.navigate = controller.navigate
    # Start intercepting click events.
    options =
      external_selectors: ['[rel="external"]']
      back_selectors: ['[rel="back"]']
      bind_events: 'click submit'
    interceptor = new mobone.event.Interceptor options
    # Start handling history change events.
    Backbone.history.start pushState: true
    # Show the UI.
    $(document.body).show()
  


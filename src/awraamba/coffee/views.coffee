# ...
define 'views', (exports, root) ->
  
  # Two utility functions to convert seconds into a formated time string,
  # e.g.: from `64` into `"01:04"`.
  Number::toTwoDigitString = ->
    n = this
    s = if n < 10 then '0' + n else '' + n
    s.substring 0, 2
  
  Number::toMMSS = ->
    s = this
    m = 0
    if s >= 60
      m = parseInt(s / 60)
      s -= m * 60
    s = Math.round s
    m.toTwoDigitString() + ':' + s.toTwoDigitString()
  
  
  # `Resizer` binds to throttled window resize events to resize ``@el`` to
  # the viewport dimensions.
  class Resizer extends Backbone.View
    defaults:
      w: 0
      h: 80
    resize: ->
      $target = @$el
      $target.height window.innerHeight - @options.h
      $target.width window.innerWidth - @options.w
    
    initialize: ->
      @options = _.defaults @options, @defaults
      resize = => @resize()
      throttled_resize = _.throttle resize, 250
      $(window).bind 'resize', throttled_resize
    
  
  # Show the intro screen and handle clicks on the enter link by navigating to
  # the request path stored in its model value.
  class IntroView extends Backbone.View
    events:
      'dblclick #intro-enter-link'  : 'next'
      'click #intro-enter-link'     : 'next'
    
    next: ->
      path = @model.get 'value'
      if not path or path.startsWith('/intro')
        path = '/'
      app.navigate path, true
      false
    
    initialize: ->
      $target = $ @el
      $container = $ "#intro-video-container"
      @player = Popcorn "#intro-video"
      # Before hide, pause and rewind the video player and fade the video out.
      # When the fade is done, rewind to the beginning.
      @bind 'beforehide', => 
        @player.pause()
        $container.animate opacity: 0, 750, =>
          @player.currentTime 0
      @bind 'hide', => 
        $target.hide()
      @bind 'show', =>
        $container.css opacity: 0
        $target.show()
      # After show, pause for two seconds, then fade the video in and play
      # from the beginning.
      @bind 'aftershow', =>
        window.setTimeout =>
            $container.animate opacity: 1, 1500, =>
               @player.play 0
          , 2000
    
  
  # Embed and hook up the krpano panorama and switch to the selected scenes when
  # the scene name stored in the model value changes.
  class ExploreView extends Backbone.View
    defaults:
      scene_name: 'village-square'
    
    render: =>
      # Update the panorama location.
      scene_name = @model.get 'value'
      scene_name = @options.scene_name if not scene_name?
      @krpano.call "loadscene('scene_#{scene_name}', null, MERGE);"
    
    initialize: ->
      _.defaults @options, @defaults
      # Resize the container manually.
      resizer = new views.Resizer el: $('#explore-panorama')
      resizer.resize()
      # Hide and show *without* a repaint to keep the panorama state.
      # XXX cross browser testing.
      $target = $ @el
      @bind 'hide', => $target.css visibility: 'hidden'
      @bind 'show', => $target.css visibility: 'visible'
      # Bind once to the krpano "load event".
      root.krpano_loaded = =>
        # Before starting the fade out, we freeze the view.  After the fade out,
        # we re-enable the user interaction.
        @krpano = $('#krpanoSWFObject').get 0
        @bind 'beforehide', => @krpano.call "freezeview(true);" if @krpano.call?
        @bind 'aftershow', => @krpano.call "freezeview(false);" if @krpano.call?
        # Show the initial scene and change scene when the model value changes.
        @model.bind 'change', @render
        @render()
        # Ignore future "events"
        root.krpano_loaded = $.noop
      # Embed the krpano viewer.
      embedpano swf: '/tour/tour.swf', target: 'explore-panorama', xml: '/tour/tour.xml'
    
  
  # Simple container menu -- does nothing.
  class WatchView extends Backbone.View
    render: => # pass
    initialize: ->
      # Show hide using display none.
      $target = $ @el
      @bind 'hide', => $target.hide()
      @bind 'show', => $target.show()
    
  
  # `ReactionsCollection` keeps reactions in timecode order.
  class ReactionsCollection extends Backbone.Collection
    # XXX sort is by slug:mmss:timecode:created.  This needs to reflect the
    # themes sort order, i.e.: which order do we want the themes on the page,
    # as opposed to just using slug.  This may require back end tweaks to
    # return the theme_sort_order or some such in the reaction JSON.
    comparator: (m) -> 
      tc = m.get 'timecode'
      "#{m.get 'theme_slug'}:#{tc.toMMSS()}:#{tc}:#{m.get 'c'}"
    
  
  # `ThreadView` renders an individual thread.
  class ThreadView extends Backbone.View
    tagName: 'li'
    className: 'thread'
    render: ->
      # Insert the markup for this thread.
      $target = $ @el
      $target.html templates.thread_content @model.toJSON()
      # Toggle the reaction info on thread click.
      @$('a.thread').click ->
        $(this).next().slideToggle 'normal'
        false
    
    initialize: ->
      @model.view = this
      @render()
    
  
  # `ThreadListingsView` renders a listing of threads.
  class ThreadListingsView extends Backbone.View
    # When a thread is added, render it at the top of the listings.
    handle_add: (model) =>
      view = new ThreadView model: model
      $(@el).prepend(view.el)
    
    # When a thread is removed, remove it from the listings.
    handle_remove: (model_or_models) =>
      if model_or_models instanceof Backbone.Model
        models = [model_or_models]
      else
        models = model_or_models
      for model in models
        model.view.remove()
    
    # When the listings are reset, render the new threads.
    handle_reset: (models) =>
      $(@el).empty()
      models.each @handle_add
    
    initialize: ->
      @collection.bind 'add', @handle_add
      @collection.bind 'remove', @handle_remove
      @collection.bind 'reset', @handle_reset
    
  
  # Apply the Popcorn.js viewer to the `<video id="theme-video" /> element and
  # switch video when the selected theme changes.  Handle video timecode events
  # to control which threads should be rendered below the video.
  class ThemeView extends Backbone.View
    defaults:
      extensions: ['mp4', 'ogv', 'webm']
      videos_path: 'http://videos.mozilla.org/serv/webmademovies/'
    events:
      'click #react-btn'        : 'enable_react_mode'
      'click #watch-btn'        : 'enable_watch_mode'
      'submit #react-form'      : 'submit_reaction'
    reactions: null
    react_mode: false
    previous_time: null
    current_time: 0
    next_thread_index: 0
    was_playing: false
    # If we want to seek to a position, we need the player to be ready.
    play_when_ready: (timecode) ->
      if timecode
        if @player.readyState() > 1
          @player.currentTime timecode
          @player.play()
        else
          @player.listen 'canplay', => 
            @player.unlisten 'canplay'
            @player.currentTime timecode
            @player.play()
      else
        @player.play()
    
    # Control which threads are rendered based on the current time and update
    # the timecode input with the current time value.
    handle_time_update: =>
      @previous_time = @current_time
      @current_time = @player.currentTime()
      if @current_time isnt @previous_time
        # If the new time is less than the previous time, loop through the
        # rendered_threads, removing those that shouldn't be shown yet.
        if @current_time < @previous_time
          to_remove = []
          index = @rendered_threads.length - 1
          while true
            thread = @rendered_threads.at index
            if thread? and thread.get('timecode') > @current_time
              to_remove.push thread
              index -= 1
            else
              break
          if to_remove
            @next_thread_index -= to_remove.length
            @rendered_threads.remove to_remove
        # If the new time is greater than the previous time, loop through the
        # current_threads that haven't been rendered, adding those that should be.
        else
          while true
            thread = @current_threads.at @next_thread_index
            if thread? and thread.get('timecode') < @current_time
              @rendered_threads.add thread.toJSON()
              @next_thread_index += 1
            else
              break
        # Render the current time.
        @current_time_input.attr 'data-value', @current_time
        @current_time_input.val @current_time.toMMSS()
    
    # Toggle modes.
    enable_react_mode: =>
      @was_playing = true # XXX this is assumed in the absence of a playstate
      @player.pause()
      @react_btn.hide()
      @watch_btn.show()
      @react_ui.show()
      @react_mode = true
      false
    
    enable_watch_mode: =>
      @react_mode = false
      @react_ui.hide()
      @watch_btn.hide()
      @react_btn.show()
      if @was_playing
        @player.play()
      false
    
    # Handle the form submission.
    submit_reaction: =>
      # Swap the mm:ss and the secs values around for a moment.
      _current_value = @current_time_input.val()
      @current_time_input.val @current_time_input.attr 'data-value'
      # Get the form data.
      slug_param = '&theme_slug=' + @model.get('value').split('/')[0]
      data = @react_form.serialize() + slug_param
      # Swap the mm:ss back in.
      @current_time_input.val _current_value
      $.ajax
        type: 'POST'
        url: @react_form.attr 'action'
        data: data
        dataType: 'json'
        success: (data) =>
          # Insert and highlight the thread.
          @current_threads.add data
          @rendered_threads.add data
          @next_thread_index += 1
          @$('li.thread:first').highlight()
      false
    
    reset: (reactions) =>
      @was_playing = false
      @previous_time = null
      @current_time = 0
      @next_thread_index = 0
      if reactions?
        @rendered_threads.each (m) -> m.view.remove()
        @rendered_threads.reset()
        @current_threads.reset reactions
    
    render: =>
      theme = @model.get 'value'
      if theme?
        # `theme` can be a slug like `gender` or a slug and a timecode, e.g.:
        # `gender/12.134`.
        parts = theme.split '/'
        theme = parts[0]
        timecode = 0
        if parts.length > 1
          timecode_str = parts[1]
          if parseFloat(timecode_str).toString() is timecode_str
            timecode = parseFloat timecode_str
        # Set srcs.
        path = @options.videos_path
        exts = @options.extensions
        has_changed = false
        @sources.each (i) -> 
          $source = $ this
          existing_src = $source.attr 'src'
          # XXX fake sources for now using mozilla sources
          _theme = if theme is 'gender' then 'thankyou' else 'popcorntest'
          new_src = "#{path}#{_theme}.#{exts[i]}"
          if new_src isnt existing_src
            $source.attr 'src', new_src
            has_changed = true
        if has_changed
          # Get reactions for this theme using AJAX.
          data = theme_slug: theme
          $.getJSON '/api/reactions/', data, (reactions) =>
            # XXX we have to *not* use an id, to avoid "adding the same model to
            # a collection twice", for some strange Backbine reason.
            for item in reactions
              item['reaction_id'] = item['id']
              delete item['id']
            @reset reactions
            @player.load()
            @play_when_ready timecode
        else
          @play_when_ready timecode
    
    initialize: ->
      _.defaults @options, @defaults
      # Show hide using display none.
      $target = $ @el
      @bind 'hide', => $target.hide()
      @bind 'show', => $target.show()
      # Initialise Popcorn.js player.
      @video = @$ "#theme-video"
      @player = Popcorn "#theme-video"
      @player.controls true
      @player.media.autoplay = true
      @player.listen 'timeupdate', @handle_time_update
      @player.listen 'seeked', @handle_time_update
      # Get a handle on the <source /> elements.
      @sources = @$ '#theme-video > source'
      # Get a handle on the react controls.
      @react_btn = @$ '#react-btn'
      @watch_btn = @$ '#watch-btn'
      @react_ui = @$ '#react-ui'
      @react_form = @$ '#react-form'
      @current_time_input = @$ '#timecode'
      # Create a `ThreadListingsView` and collections for reactions.
      @current_threads = new ReactionsCollection
      @rendered_threads = new ReactionsCollection
      @thread_listings = new ThreadListingsView
        el: '#thread-listings'
        collection: @rendered_threads
      # Pause and play on before hide and after show.
      @bind 'beforehide', => 
        @player.currentTime 0
        @player.pause()
      @bind 'aftershow', => @player.play()
      # Bind to theme changes and render.
      @model.bind 'change', @render
      @render()
    
  
  # Render the interactive scarf.
  class InteractView extends Backbone.View
    # XXX the logic here is pretty primitive: we'll need to re-implement when the
    # scraf design is developed, e.g.: to handle new reactions, how we want to
    # display individual reactions, infinite scroll, etc.
    render: =>
      $.getJSON '/api/reactions/', (reactions) => @threads.reset reactions
    
    initialize: ->
      @model.set 'value', NaN
      @model.bind 'change', @render
      $target = $ @el
      @bind 'afterhide', => $target.hide()
      @bind 'beforeshow', => $target.show()
      @threads = new ReactionsCollection
      @thread_listings = new ThreadListingsView
        el: '#scarf-listings'
        collection: @threads
    
  
  # Render the user's profile info and their activity.
  class ProfileView extends Backbone.View
    render: =>
      @threads.reset()
      username = @model.get 'value'
      md5_hash = Crypto.MD5 username.toLowerCase(), asString: true
      @title.text "@#{username}'s Profile"
      @avatar.attr 'src', '//www.gravatar.com/avatar/' + md5_hash
      $.getJSON '/api/reactions/', (reactions) => @threads.reset reactions
    
    initialize: ->
      @model.bind 'change', @render
      $target = $ @el
      @title = @$ '#profile-title'
      @avatar = @$ '#profile-avatar'
      @bind 'afterhide', => $target.hide()
      @bind 'beforeshow', => $target.show()
      @threads = new ReactionsCollection
      @thread_listings = new ThreadListingsView
        el: '#profile-listings'
        collection: @threads
    
  
  exports.Resizer = Resizer
  exports.IntroView = IntroView
  exports.ExploreView = ExploreView
  exports.WatchView = WatchView
  exports.ThemeView = ThemeView
  exports.InteractView = InteractView
  exports.ProfileView = ProfileView


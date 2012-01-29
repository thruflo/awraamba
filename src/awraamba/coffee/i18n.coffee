# Use `i18n._()` to translate message strings, if a translated version of the
# string has been provided using ``i18n.register_strings()``, e.g.:
# 
#     i18n.register_strings hello: 'bonjour'
#     i18n._ 'hello'
#     => 'bonjour'
# 
define 'i18n', (exports, root) ->
  
  _msg_strings = {}
  
  register_strings = (data) -> 
    _msg_strings = _.update(_msg_strings, data)
  
  translate = (s) -> 
    if s of _msg_strings then _msg_strings[s] else s
  
  exports.register_strings = register_strings
  exports._ = exports.translate = translate


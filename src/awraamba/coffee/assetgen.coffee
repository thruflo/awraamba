# Use `assetgen.static_url()` to unpack static paths into expanded urls using the
# pyramid_assetgen machinery, e.g.:
# 
#     assetgen.add_manifest '/static', 'foo.js': 'foo-5678565f87ds5f68758.js'
#     assetgen.static_url '/static/foo.js'
#     => '/static/foo-5678565f87ds5f68758.js'
# 
# XXX: this needs to have tests and be integrated into `pyramid_assetgen`.
define 'assetgen', (exports, root) ->
  
  if not String::startsWith?
    String::startsWith = (s) -> @indexOf(s) is 0
  if not String::endsWith?
    String::endsWith = (s) -> -1 isnt @indexOf s, @length - s.length
  
  _manifests = {}
  
  add_manifest = (path, data) -> 
    path = if not path.endsWith('/') then path + '/' else path
    _manifests[path] = data
  
  static_path = (path) ->
    for k, v of _manifests
      if path.startsWith k 
        parts = path.split k
        relative_path = parts[1...parts.length].join(k)
        if relative_path of v
          relative_path = v[relative_path]
        return k + relative_path
    path
  
  exports.add_manifest = add_manifest
  exports.static_path = static_path


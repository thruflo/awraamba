<%inherit file="base.mako"/>

% for item in ('intro', 'explore', 'watch', 'interact'):
  <!-- 
    
    ${item.title()}
    
    
  -->
  <%include file="partials/${item}.mako" />
% endfor

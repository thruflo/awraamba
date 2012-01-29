<%inherit file="base.mako"/>

% for item in ('intro', 'explore', 'watch', 'theme', 'interact', 'profile'):
  <!-- 
    
    ${item.title()}
    
    
  -->
  <%include file="partials/${item}.mako" />
% endfor

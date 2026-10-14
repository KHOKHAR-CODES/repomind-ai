(function(){
  const c=document.createElement('canvas');
  c.style.position='absolute'; c.style.top='0'; c.style.left='0';
  c.style.width='100%'; c.style.height='100%'; c.style.pointerEvents='none';
  c.style.zIndex='0';
  const gl=c.getContext('webgl',{alpha:true,premultipliedAlpha:false,antialias:false})||c.getContext('experimental-webgl',{alpha:true,premultipliedAlpha:false,antialias:false});
  if(!gl){console.warn('WebGL unavailable'); return;}
  function resize(){const dpr=Math.min(window.devicePixelRatio||1,2); if(!c.parentElement)return; c.width=c.parentElement.clientWidth*dpr; c.height=c.parentElement.clientHeight*dpr; gl.viewport(0,0,c.width,c.height);}
  function hexToRgb(h){const m=/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(h); return m?[parseInt(m[1],16)/255,parseInt(m[2],16)/255,parseInt(m[3],16)/255]:[1,1,1];}
  const vert=`attribute vec2 a_pos; void main(){gl_Position=vec4(a_pos,0,1);}`;
  const frag=`precision mediump float; uniform float u_time; uniform vec2 u_res; uniform vec3 u_color; uniform float u_speed; uniform float u_spread; uniform float u_length; uniform float u_pulse; uniform float u_distort; uniform float u_noise; void main(){vec2 p=gl_FragCoord.xy/u_res; float dAngle=dot(normalize(p-vec2(0.5,0.0)),vec2(0,1)); dAngle+=u_distort*sin(u_time*1.5+p.y*3.0); float dist=length(p-vec2(0.5,0.0)); float spread=pow(max(dAngle,0.0),1.0/max(u_spread,0.001)); float falloff=clamp((u_length*2.0-dist)/(u_length*2.0),0.0,1.0); float pulse=u_pulse>0.5?(0.85+0.15*sin(u_time*u_speed*4.0)):1.0; float base=clamp(0.5+0.2*sin(dAngle*45.0+u_time*u_speed)+0.3*cos(-dAngle*31.0+u_time*u_speed*0.8),0.0,1.0); float s=base*falloff*spread*pulse*1.4; vec3 col=u_color*s; if(u_noise>0.0){float n=fract(sin(dot(p,vec2(12.98,78.23)))*43758.5453); col*=0.8+0.2*n;} gl_FragColor=vec4(col,s);}`;
  function compile(t,tv){const s=gl.createShader(t); gl.shaderSource(s,tv); gl.compileShader(s); return s;}
  const prog=gl.createProgram(); gl.attachShader(prog,compile(gl.VERTEX_SHADER,vert)); gl.attachShader(prog,compile(gl.FRAGMENT_SHADER,frag)); gl.linkProgram(prog); gl.useProgram(prog);
  const buf=gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER,buf); gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
  const attr=gl.getAttribLocation(prog,'a_pos'); gl.enableVertexAttribArray(attr); gl.vertexAttribPointer(attr,2,gl.FLOAT,false,0,0);
  const u_time=gl.getUniformLocation(prog,'u_time'); const u_res=gl.getUniformLocation(prog,'u_res'); const u_color=gl.getUniformLocation(prog,'u_color');
  const u_speed=gl.getUniformLocation(prog,'u_speed'); const u_spread=gl.getUniformLocation(prog,'u_spread'); const u_length=gl.getUniformLocation(prog,'u_length');
  const u_pulse=gl.getUniformLocation(prog,'u_pulse'); const u_distort=gl.getUniformLocation(prog,'u_distort'); const u_noise=gl.getUniformLocation(prog,'u_noise');
  function loop(t){if(!gl) return; resize(); gl.uniform1f(u_time,t*0.001); gl.uniform2f(u_res,c.width,c.height); gl.uniform3f(u_color,...hexToRgb('#00ff88')); gl.uniform1f(u_speed,0.8); gl.uniform1f(u_spread,0.9); gl.uniform1f(u_length,1.4); gl.uniform1f(u_pulse,1.0); gl.uniform1f(u_distort,0.05); gl.uniform1f(u_noise,0.02); gl.drawArrays(gl.TRIANGLE_STRIP,0,4); requestAnimationFrame(loop);}
  requestAnimationFrame(loop);
  const targets=[document.querySelector('.welcome-panel'), document.querySelector('.ask-workspace')];
  targets.forEach(el=>{if(el){el.style.position='relative'; el.insertBefore(c.cloneNode(true),el.firstChild); resize();}});
})();

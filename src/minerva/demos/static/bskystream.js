(function() {
function e(a) {
  throw a;
}
var h = void 0, j = !0, k = null, m = !1;
function aa() {
  return function() {
  }
}
function ba(a) {
  return function(b) {
    this[a] = b
  }
}
function p(a) {
  return function() {
    return this[a]
  }
}
function q(a) {
  return function() {
    return a
  }
}
var t;
var ca = ca || {}, u = this;
function da(a) {
  for(var a = a.split("."), b = u, c;c = a.shift();) {
    if(b[c] != k) {
      b = b[c]
    }else {
      return k
    }
  }
  return b
}
function v() {
}
function ea(a) {
  a.Oa = function() {
    return a.Td ? a.Td : a.Td = new a
  }
}
function fa(a) {
  var b = typeof a;
  if("object" == b) {
    if(a) {
      if(a instanceof Array) {
        return"array"
      }
      if(a instanceof Object) {
        return b
      }
      var c = Object.prototype.toString.call(a);
      if("[object Window]" == c) {
        return"object"
      }
      if("[object Array]" == c || "number" == typeof a.length && "undefined" != typeof a.splice && "undefined" != typeof a.propertyIsEnumerable && !a.propertyIsEnumerable("splice")) {
        return"array"
      }
      if("[object Function]" == c || "undefined" != typeof a.call && "undefined" != typeof a.propertyIsEnumerable && !a.propertyIsEnumerable("call")) {
        return"function"
      }
    }else {
      return"null"
    }
  }else {
    if("function" == b && "undefined" == typeof a.call) {
      return"object"
    }
  }
  return b
}
function w(a) {
  return a !== h
}
function ga(a) {
  return"array" == fa(a)
}
function ha(a) {
  var b = fa(a);
  return"array" == b || "object" == b && "number" == typeof a.length
}
function ia(a) {
  return ja(a) && "function" == typeof a.getFullYear
}
function x(a) {
  return"string" == typeof a
}
function z(a) {
  return"function" == fa(a)
}
function ja(a) {
  var b = typeof a;
  return"object" == b && a != k || "function" == b
}
function B(a) {
  return a[ka] || (a[ka] = ++la)
}
var ka = "closure_uid_" + Math.floor(2147483648 * Math.random()).toString(36), la = 0;
function ma(a, b, c) {
  return a.call.apply(a.bind, arguments)
}
function na(a, b, c) {
  a || e(Error());
  if(2 < arguments.length) {
    var d = Array.prototype.slice.call(arguments, 2);
    return function() {
      var c = Array.prototype.slice.call(arguments);
      Array.prototype.unshift.apply(c, d);
      return a.apply(b, c)
    }
  }
  return function() {
    return a.apply(b, arguments)
  }
}
function C(a, b, c) {
  C = Function.prototype.bind && -1 != Function.prototype.bind.toString().indexOf("native code") ? ma : na;
  return C.apply(k, arguments)
}
function oa(a, b) {
  var c = Array.prototype.slice.call(arguments, 1);
  return function() {
    var b = Array.prototype.slice.call(arguments);
    b.unshift.apply(b, c);
    return a.apply(this, b)
  }
}
var pa = Date.now || function() {
  return+new Date
};
function E(a, b) {
  function c() {
  }
  c.prototype = b.prototype;
  a.g = b.prototype;
  a.prototype = new c;
  a.prototype.constructor = a
}
;function F(a) {
  Error.captureStackTrace ? Error.captureStackTrace(this, F) : this.stack = Error().stack || "";
  a && (this.message = String(a))
}
E(F, Error);
F.prototype.name = "CustomError";
function qa(a, b) {
  for(var c = 1;c < arguments.length;c++) {
    var d = String(arguments[c]).replace(/\$/g, "$$$$"), a = a.replace(/\%s/, d)
  }
  return a
}
function ra(a, b) {
  return a.replace(/(\r\n|\r|\n)/g, b ? "<br />" : "<br>")
}
function sa(a) {
  if(!ta.test(a)) {
    return a
  }
  -1 != a.indexOf("&") && (a = a.replace(ua, "&amp;"));
  -1 != a.indexOf("<") && (a = a.replace(va, "&lt;"));
  -1 != a.indexOf(">") && (a = a.replace(wa, "&gt;"));
  -1 != a.indexOf('"') && (a = a.replace(xa, "&quot;"));
  return a
}
var ua = /&/g, va = /</g, wa = />/g, xa = /\"/g, ta = /[&<>\"]/;
function ya(a) {
  return ra(a.replace(/  /g, " &#160;"), h)
}
function za(a, b) {
  for(var c = 0, d = String(a).replace(/^[\s\xa0]+|[\s\xa0]+$/g, "").split("."), g = String(b).replace(/^[\s\xa0]+|[\s\xa0]+$/g, "").split("."), f = Math.max(d.length, g.length), i = 0;0 == c && i < f;i++) {
    var l = d[i] || "", n = g[i] || "", s = RegExp("(\\d*)(\\D*)", "g"), A = RegExp("(\\d*)(\\D*)", "g");
    do {
      var r = s.exec(l) || ["", "", ""], y = A.exec(n) || ["", "", ""];
      if(0 == r[0].length && 0 == y[0].length) {
        break
      }
      c = ((0 == r[1].length ? 0 : parseInt(r[1], 10)) < (0 == y[1].length ? 0 : parseInt(y[1], 10)) ? -1 : (0 == r[1].length ? 0 : parseInt(r[1], 10)) > (0 == y[1].length ? 0 : parseInt(y[1], 10)) ? 1 : 0) || ((0 == r[2].length) < (0 == y[2].length) ? -1 : (0 == r[2].length) > (0 == y[2].length) ? 1 : 0) || (r[2] < y[2] ? -1 : r[2] > y[2] ? 1 : 0)
    }while(0 == c)
  }
  return c
}
;function Aa(a, b) {
  b.unshift(a);
  F.call(this, qa.apply(k, b));
  b.shift();
  this.$g = a
}
E(Aa, F);
Aa.prototype.name = "AssertionError";
function Ba(a, b) {
  e(new Aa("Failure" + (a ? ": " + a : ""), Array.prototype.slice.call(arguments, 1)))
}
;var Ca;
Ca = q(j);
var Da, Ea, Fa, Ga;
function Ha() {
  return u.navigator ? u.navigator.userAgent : k
}
Ga = Fa = Ea = Da = m;
var Ia;
if(Ia = Ha()) {
  var Ja = u.navigator;
  Da = 0 == Ia.indexOf("Opera");
  Ea = !Da && -1 != Ia.indexOf("MSIE");
  Fa = !Da && -1 != Ia.indexOf("WebKit");
  Ga = !Da && !Fa && "Gecko" == Ja.product
}
var Ka = Da, G = Ea, H = Ga, I = Fa, La = u.navigator, Ma = -1 != (La && La.platform || "").indexOf("Mac"), Na;
a: {
  var Oa = "", Pa;
  if(Ka && u.opera) {
    var Qa = u.opera.version, Oa = "function" == typeof Qa ? Qa() : Qa
  }else {
    if(H ? Pa = /rv\:([^\);]+)(\)|;)/ : G ? Pa = /MSIE\s+([^\);]+)(\)|;)/ : I && (Pa = /WebKit\/(\S+)/), Pa) {
      var Ra = Pa.exec(Ha()), Oa = Ra ? Ra[1] : ""
    }
  }
  if(G) {
    var Sa, Ta = u.document;
    Sa = Ta ? Ta.documentMode : h;
    if(Sa > parseFloat(Oa)) {
      Na = String(Sa);
      break a
    }
  }
  Na = Oa
}
var Ua = {};
function J(a) {
  return Ua[a] || (Ua[a] = 0 <= za(Na, a))
}
var Va = {};
function Wa(a) {
  return Va[a] || (Va[a] = G && !!document.documentMode && document.documentMode >= a)
}
;function Xa() {
}
var Ya = 0;
t = Xa.prototype;
t.key = 0;
t.Ia = m;
t.rc = m;
t.mb = function(a, b, c, d, g, f) {
  z(a) ? this.Xd = j : a && a.handleEvent && z(a.handleEvent) ? this.Xd = m : e(Error("Invalid listener argument"));
  this.Wa = a;
  this.pe = b;
  this.src = c;
  this.type = d;
  this.capture = !!g;
  this.Ob = f;
  this.rc = m;
  this.key = ++Ya;
  this.Ia = m
};
t.handleEvent = function(a) {
  return this.Xd ? this.Wa.call(this.Ob || this.src, a) : this.Wa.handleEvent.call(this.Wa, a)
};
function Za(a, b) {
  for(var c in a) {
    b.call(h, a[c], c, a)
  }
}
function $a(a) {
  var b = [], c = 0, d;
  for(d in a) {
    b[c++] = a[d]
  }
  return b
}
function ab(a) {
  var b = [], c = 0, d;
  for(d in a) {
    b[c++] = d
  }
  return b
}
var bb = "constructor hasOwnProperty isPrototypeOf propertyIsEnumerable toLocaleString toString valueOf".split(" ");
function cb(a, b) {
  for(var c, d, g = 1;g < arguments.length;g++) {
    d = arguments[g];
    for(c in d) {
      a[c] = d[c]
    }
    for(var f = 0;f < bb.length;f++) {
      c = bb[f], Object.prototype.hasOwnProperty.call(d, c) && (a[c] = d[c])
    }
  }
}
;var db = !G || Wa(9), eb = !G || Wa(9), fb = G && !J("9");
!I || J("528");
H && J("1.9b") || G && J("8") || Ka && J("9.5") || I && J("528");
H && !J("8") || G && J("9");
var K = Array.prototype, gb = K.indexOf ? function(a, b, c) {
  return K.indexOf.call(a, b, c)
} : function(a, b, c) {
  c = c == k ? 0 : 0 > c ? Math.max(0, a.length + c) : c;
  if(x(a)) {
    return!x(b) || 1 != b.length ? -1 : a.indexOf(b, c)
  }
  for(;c < a.length;c++) {
    if(c in a && a[c] === b) {
      return c
    }
  }
  return-1
}, hb = K.forEach ? function(a, b, c) {
  K.forEach.call(a, b, c)
} : function(a, b, c) {
  for(var d = a.length, g = x(a) ? a.split("") : a, f = 0;f < d;f++) {
    f in g && b.call(c, g[f], f, a)
  }
}, ib = K.filter ? function(a, b, c) {
  return K.filter.call(a, b, c)
} : function(a, b, c) {
  for(var d = a.length, g = [], f = 0, i = x(a) ? a.split("") : a, l = 0;l < d;l++) {
    if(l in i) {
      var n = i[l];
      b.call(c, n, l, a) && (g[f++] = n)
    }
  }
  return g
}, jb = K.map ? function(a, b, c) {
  return K.map.call(a, b, c)
} : function(a, b, c) {
  for(var d = a.length, g = Array(d), f = x(a) ? a.split("") : a, i = 0;i < d;i++) {
    i in f && (g[i] = b.call(c, f[i], i, a))
  }
  return g
}, kb = K.some ? function(a, b, c) {
  return K.some.call(a, b, c)
} : function(a, b, c) {
  for(var d = a.length, g = x(a) ? a.split("") : a, f = 0;f < d;f++) {
    if(f in g && b.call(c, g[f], f, a)) {
      return j
    }
  }
  return m
}, lb = K.every ? function(a, b, c) {
  return K.every.call(a, b, c)
} : function(a, b, c) {
  for(var d = a.length, g = x(a) ? a.split("") : a, f = 0;f < d;f++) {
    if(f in g && !b.call(c, g[f], f, a)) {
      return m
    }
  }
  return j
};
function mb(a, b) {
  return 0 <= gb(a, b)
}
function nb(a, b) {
  var c = gb(a, b);
  0 <= c && K.splice.call(a, c, 1)
}
function ob(a) {
  return K.concat.apply(K, arguments)
}
function pb(a) {
  var b = a.length;
  if(0 < b) {
    for(var c = Array(b), d = 0;d < b;d++) {
      c[d] = a[d]
    }
    return c
  }
  return[]
}
function qb(a, b, c) {
  return 2 >= arguments.length ? K.slice.call(a, b) : K.slice.call(a, b, c)
}
function rb(a, b) {
  return a > b ? 1 : a < b ? -1 : 0
}
;var sb = {Zf:"click", dg:"dblclick", zg:"mousedown", Dg:"mouseup", Cg:"mouseover", Bg:"mouseout", Ag:"mousemove", Pg:"selectstart", ug:"keypress", tg:"keydown", vg:"keyup", Xf:"blur", ng:"focus", eg:"deactivate", og:G ? "focusin" : "DOMFocusIn", pg:G ? "focusout" : "DOMFocusOut", Yf:"change", Og:"select", Qg:"submit", sg:"input", Kg:"propertychange", kg:"dragstart", fg:"drag", hg:"dragenter", jg:"dragover", ig:"dragleave", lg:"drop", gg:"dragend", Ug:"touchstart", Tg:"touchmove", Sg:"touchend", Rg:"touchcancel", 
Wf:"beforeunload", ag:"contextmenu", mg:"error", rg:"help", wg:"load", xg:"losecapture", Lg:"readystatechange", Mg:"resize", Ng:"scroll", Wg:"unload", qg:"hashchange", Gg:"pagehide", Hg:"pageshow", Jg:"popstate", bg:"copy", Ig:"paste", cg:"cut", Tf:"beforecopy", Uf:"beforecut", Vf:"beforepaste", Fg:"online", Eg:"offline", yg:"message", $f:"connect", Vg:I ? "webkitTransitionEnd" : Ka ? "oTransitionEnd" : "transitionend"};
function L() {
  0 != tb && (this.Xg = Error().stack, ub[B(this)] = this)
}
var tb = 0, ub = {};
L.prototype.$ = m;
L.prototype.b = function() {
  if(!this.$ && (this.$ = j, this.c(), 0 != tb)) {
    var a = B(this);
    delete ub[a]
  }
};
L.prototype.c = function() {
  this.Ve && vb.apply(k, this.Ve);
  if(this.je) {
    for(;this.je.length;) {
      this.je.shift()()
    }
  }
};
function vb(a) {
  for(var b = 0, c = arguments.length;b < c;++b) {
    var d = arguments[b];
    ha(d) ? vb.apply(k, d) : d && "function" == typeof d.b && d.b()
  }
}
;function wb(a, b) {
  this.type = a;
  this.currentTarget = this.target = b
}
t = wb.prototype;
t.c = aa();
t.b = aa();
t.Ha = m;
t.defaultPrevented = m;
t.ac = j;
t.stopPropagation = function() {
  this.Ha = j
};
t.preventDefault = function() {
  this.defaultPrevented = j;
  this.ac = m
};
function xb(a) {
  a.stopPropagation()
}
;function yb(a) {
  yb[" "](a);
  return a
}
yb[" "] = v;
function zb(a, b) {
  a && this.mb(a, b)
}
E(zb, wb);
var Ab = [1, 4, 2];
t = zb.prototype;
t.target = k;
t.relatedTarget = k;
t.offsetX = 0;
t.offsetY = 0;
t.clientX = 0;
t.clientY = 0;
t.screenX = 0;
t.screenY = 0;
t.button = 0;
t.keyCode = 0;
t.charCode = 0;
t.ctrlKey = m;
t.altKey = m;
t.shiftKey = m;
t.metaKey = m;
t.Vc = m;
t.ma = k;
t.mb = function(a, b) {
  var c = this.type = a.type;
  wb.call(this, c);
  this.target = a.target || a.srcElement;
  this.currentTarget = b;
  var d = a.relatedTarget;
  if(d) {
    if(H) {
      var g;
      a: {
        try {
          yb(d.nodeName);
          g = j;
          break a
        }catch(f) {
        }
        g = m
      }
      g || (d = k)
    }
  }else {
    "mouseover" == c ? d = a.fromElement : "mouseout" == c && (d = a.toElement)
  }
  this.relatedTarget = d;
  this.offsetX = I || a.offsetX !== h ? a.offsetX : a.layerX;
  this.offsetY = I || a.offsetY !== h ? a.offsetY : a.layerY;
  this.clientX = a.clientX !== h ? a.clientX : a.pageX;
  this.clientY = a.clientY !== h ? a.clientY : a.pageY;
  this.screenX = a.screenX || 0;
  this.screenY = a.screenY || 0;
  this.button = a.button;
  this.keyCode = a.keyCode || 0;
  this.charCode = a.charCode || ("keypress" == c ? a.keyCode : 0);
  this.ctrlKey = a.ctrlKey;
  this.altKey = a.altKey;
  this.shiftKey = a.shiftKey;
  this.metaKey = a.metaKey;
  this.Vc = Ma ? a.metaKey : a.ctrlKey;
  this.state = a.state;
  this.ma = a;
  a.defaultPrevented && this.preventDefault();
  delete this.Ha
};
function Bb(a) {
  return db ? 0 == a.ma.button : "click" == a.type ? j : !!(a.ma.button & Ab[0])
}
t.stopPropagation = function() {
  zb.g.stopPropagation.call(this);
  this.ma.stopPropagation ? this.ma.stopPropagation() : this.ma.cancelBubble = j
};
t.preventDefault = function() {
  zb.g.preventDefault.call(this);
  var a = this.ma;
  if(a.preventDefault) {
    a.preventDefault()
  }else {
    if(a.returnValue = m, fb) {
      try {
        if(a.ctrlKey || 112 <= a.keyCode && 123 >= a.keyCode) {
          a.keyCode = -1
        }
      }catch(b) {
      }
    }
  }
};
t.c = aa();
var Cb = {}, M = {}, Db = {}, Eb = {};
function N(a, b, c, d, g) {
  if(b) {
    if(ga(b)) {
      for(var f = 0;f < b.length;f++) {
        N(a, b[f], c, d, g)
      }
      return k
    }
    var d = !!d, i = M;
    b in i || (i[b] = {d:0, Q:0});
    i = i[b];
    d in i || (i[d] = {d:0, Q:0}, i.d++);
    var i = i[d], l = B(a), n;
    i.Q++;
    if(i[l]) {
      n = i[l];
      for(f = 0;f < n.length;f++) {
        if(i = n[f], i.Wa == c && i.Ob == g) {
          if(i.Ia) {
            break
          }
          return n[f].key
        }
      }
    }else {
      n = i[l] = [], i.d++
    }
    var s = Fb, A = eb ? function(a) {
      return s.call(A.src, A.key, a)
    } : function(a) {
      a = s.call(A.src, A.key, a);
      if(!a) {
        return a
      }
    }, f = A;
    f.src = a;
    i = new Xa;
    i.mb(c, f, a, b, d, g);
    c = i.key;
    f.key = c;
    n.push(i);
    Cb[c] = i;
    Db[l] || (Db[l] = []);
    Db[l].push(i);
    a.addEventListener ? (a == u || !a.vd) && a.addEventListener(b, f, d) : a.attachEvent(b in Eb ? Eb[b] : Eb[b] = "on" + b, f);
    return c
  }
  e(Error("Invalid event type"))
}
function Gb(a, b, c, d, g) {
  if(ga(b)) {
    for(var f = 0;f < b.length;f++) {
      Gb(a, b[f], c, d, g)
    }
    return k
  }
  a = N(a, b, c, d, g);
  Cb[a].rc = j;
  return a
}
function Hb(a, b, c, d, g) {
  if(ga(b)) {
    for(var f = 0;f < b.length;f++) {
      Hb(a, b[f], c, d, g)
    }
  }else {
    if(d = !!d, a = Ib(a, b, d)) {
      for(f = 0;f < a.length;f++) {
        if(a[f].Wa == c && a[f].capture == d && a[f].Ob == g) {
          Jb(a[f].key);
          break
        }
      }
    }
  }
}
function Jb(a) {
  if(!Cb[a]) {
    return m
  }
  var b = Cb[a];
  if(b.Ia) {
    return m
  }
  var c = b.src, d = b.type, g = b.pe, f = b.capture;
  c.removeEventListener ? (c == u || !c.vd) && c.removeEventListener(d, g, f) : c.detachEvent && c.detachEvent(d in Eb ? Eb[d] : Eb[d] = "on" + d, g);
  c = B(c);
  Db[c] && (g = Db[c], nb(g, b), 0 == g.length && delete Db[c]);
  b.Ia = j;
  if(b = M[d][f][c]) {
    b.he = j, Kb(d, f, c, b)
  }
  delete Cb[a];
  return j
}
function Kb(a, b, c, d) {
  if(!d.Ub && d.he) {
    for(var g = 0, f = 0;g < d.length;g++) {
      d[g].Ia ? d[g].pe.src = k : (g != f && (d[f] = d[g]), f++)
    }
    d.length = f;
    d.he = m;
    0 == f && (delete M[a][b][c], M[a][b].d--, 0 == M[a][b].d && (delete M[a][b], M[a].d--), 0 == M[a].d && delete M[a])
  }
}
function Ib(a, b, c) {
  var d = M;
  return b in d && (d = d[b], c in d && (d = d[c], a = B(a), d[a])) ? d[a] : k
}
function Lb(a, b, c, d, g) {
  var f = 1, b = B(b);
  if(a[b]) {
    a.Q--;
    a = a[b];
    a.Ub ? a.Ub++ : a.Ub = 1;
    try {
      for(var i = a.length, l = 0;l < i;l++) {
        var n = a[l];
        n && !n.Ia && (f &= Mb(n, g) !== m)
      }
    }finally {
      a.Ub--, Kb(c, d, b, a)
    }
  }
  return Boolean(f)
}
function Mb(a, b) {
  a.rc && Jb(a.key);
  return a.handleEvent(b)
}
function Fb(a, b) {
  if(!Cb[a]) {
    return j
  }
  var c = Cb[a], d = c.type, g = M;
  if(!(d in g)) {
    return j
  }
  var g = g[d], f, i;
  if(!eb) {
    f = b || da("window.event");
    var l = j in g, n = m in g;
    if(l) {
      if(0 > f.keyCode || f.returnValue != h) {
        return j
      }
      a: {
        var s = m;
        if(0 == f.keyCode) {
          try {
            f.keyCode = -1;
            break a
          }catch(A) {
            s = j
          }
        }
        if(s || f.returnValue == h) {
          f.returnValue = j
        }
      }
    }
    s = new zb;
    s.mb(f, this);
    f = j;
    try {
      if(l) {
        for(var r = [], y = s.currentTarget;y;y = y.parentNode) {
          r.push(y)
        }
        i = g[j];
        i.Q = i.d;
        for(var D = r.length - 1;!s.Ha && 0 <= D && i.Q;D--) {
          s.currentTarget = r[D], f &= Lb(i, r[D], d, j, s)
        }
        if(n) {
          i = g[m];
          i.Q = i.d;
          for(D = 0;!s.Ha && D < r.length && i.Q;D++) {
            s.currentTarget = r[D], f &= Lb(i, r[D], d, m, s)
          }
        }
      }else {
        f = Mb(c, s)
      }
    }finally {
      r && (r.length = 0)
    }
    return f
  }
  d = new zb(b, this);
  return f = Mb(c, d)
}
var Nb = 0;
function Ob() {
  L.call(this)
}
E(Ob, L);
t = Ob.prototype;
t.vd = j;
t.Wb = k;
t.Zc = ba("Wb");
t.addEventListener = function(a, b, c, d) {
  N(this, a, b, c, d)
};
t.removeEventListener = function(a, b, c, d) {
  Hb(this, a, b, c, d)
};
t.dispatchEvent = function(a) {
  var b = a.type || a, c = M;
  if(b in c) {
    if(x(a)) {
      a = new wb(a, this)
    }else {
      if(a instanceof wb) {
        a.target = a.target || this
      }else {
        var d = a, a = new wb(b, this);
        cb(a, d)
      }
    }
    var d = 1, g, c = c[b], b = j in c, f;
    if(b) {
      g = [];
      for(f = this;f;f = f.Wb) {
        g.push(f)
      }
      f = c[j];
      f.Q = f.d;
      for(var i = g.length - 1;!a.Ha && 0 <= i && f.Q;i--) {
        a.currentTarget = g[i], d &= Lb(f, g[i], a.type, j, a) && a.ac != m
      }
    }
    if(m in c) {
      if(f = c[m], f.Q = f.d, b) {
        for(i = 0;!a.Ha && i < g.length && f.Q;i++) {
          a.currentTarget = g[i], d &= Lb(f, g[i], a.type, m, a) && a.ac != m
        }
      }else {
        for(g = this;!a.Ha && g && f.Q;g = g.Wb) {
          a.currentTarget = g, d &= Lb(f, g, a.type, m, a) && a.ac != m
        }
      }
    }
    a = Boolean(d)
  }else {
    a = j
  }
  return a
};
t.c = function() {
  Ob.g.c.call(this);
  var a, b = 0, c = a == k;
  a = !!a;
  if(this == k) {
    Za(Db, function(d) {
      for(var f = d.length - 1;0 <= f;f--) {
        var g = d[f];
        if(c || a == g.capture) {
          Jb(g.key), b++
        }
      }
    })
  }else {
    var d = B(this);
    if(Db[d]) {
      for(var d = Db[d], g = d.length - 1;0 <= g;g--) {
        var f = d[g];
        if(c || a == f.capture) {
          Jb(f.key), b++
        }
      }
    }
  }
  this.Wb = k
};
var Pb = u.window;
Nb++;
Nb++;
/*
 Portions of this code are from MochiKit, received by
 The Closure Authors under the MIT license. All other code is Copyright
 2005-2009 The Closure Authors. All Rights Reserved.
*/
function Qb(a, b) {
  this.Bb = [];
  this.qd = a;
  this.xd = b || k
}
t = Qb.prototype;
t.na = m;
t.jb = m;
t.pb = 0;
t.bd = m;
t.Re = m;
t.qc = 0;
t.cancel = function(a) {
  if(this.na) {
    this.sb instanceof Qb && this.sb.cancel()
  }else {
    if(this.t) {
      var b = this.t;
      delete this.t;
      a ? b.cancel(a) : (b.qc--, 0 >= b.qc && b.cancel())
    }
    this.qd ? this.qd.call(this.xd, this) : this.bd = j;
    this.na || this.Ma(new Rb(this))
  }
};
t.td = function(a, b) {
  Sb(this, a, b);
  this.pb--;
  0 == this.pb && this.na && Tb(this)
};
function Sb(a, b, c) {
  a.na = j;
  a.sb = c;
  a.jb = !b;
  Tb(a)
}
function Ub(a) {
  a.na && (a.bd || e(new Vb(a)), a.bd = m)
}
function Wb(a, b) {
  Ub(a);
  Sb(a, j, b)
}
t.Ma = function(a) {
  Ub(this);
  Sb(this, m, a)
};
function Xb(a, b, c, d) {
  a.Bb.push([b, c, d]);
  a.na && Tb(a)
}
function Yb(a) {
  return kb(a.Bb, function(a) {
    return z(a[1])
  })
}
function Tb(a) {
  a.ld && (a.na && Yb(a)) && (u.clearTimeout(a.ld), delete a.ld);
  a.t && (a.t.qc--, delete a.t);
  for(var b = a.sb, c = m, d = m;a.Bb.length && 0 == a.pb;) {
    var g = a.Bb.shift(), f = g[0], i = g[1], g = g[2];
    if(f = a.jb ? i : f) {
      try {
        var l = f.call(g || a.xd, b);
        w(l) && (a.jb = a.jb && (l == b || l instanceof Error), a.sb = b = l);
        b instanceof Qb && (d = j, a.pb++)
      }catch(n) {
        b = n, a.jb = j, Yb(a) || (c = j)
      }
    }
  }
  a.sb = b;
  d && a.pb && (Xb(b, C(a.td, a, j), C(a.td, a, m)), b.Re = j);
  c && (a.ld = u.setTimeout(function() {
    e(b)
  }, 0))
}
function Zb(a) {
  var b = new Qb;
  Wb(b, a);
  return b
}
function $b(a) {
  var b = new Qb;
  b.Ma(a);
  return b
}
function Vb(a) {
  F.call(this);
  this.Ue = a
}
E(Vb, F);
Vb.prototype.message = "Deferred has already fired";
Vb.prototype.name = "AlreadyCalledError";
function Rb(a) {
  F.call(this);
  this.Ue = a
}
E(Rb, F);
Rb.prototype.message = "Deferred was cancelled";
Rb.prototype.name = "CancelledError";
function ac(a) {
  this.w = a;
  this.Fb = [];
  this.Ad = [];
  this.Qe = C(this.Nf, this)
}
ac.prototype.hd = k;
ac.prototype.Nf = function() {
  this.hd = k;
  var a = this.Fb;
  this.Fb = [];
  for(var b = 0;b < a.length;b++) {
    var c = a[b], d = c[0], g = c[1], c = c[2];
    try {
      d.apply(g, c)
    }catch(f) {
      this.w.setTimeout(function() {
        e(f)
      }, 0)
    }
  }
  if(0 == this.Fb.length) {
    a = this.Ad;
    this.Ad = [];
    for(b = 0;b < a.length;b++) {
      Wb(a[b], k)
    }
  }
};
var bc = new ac(u.window);
function cc(a) {
  return z(a) || "object" == typeof a && z(a.call) && z(a.apply)
}
;function dc(a) {
  var b = [];
  ec(new fc, a, b);
  return b.join("")
}
function fc() {
  this.$b = h
}
function ec(a, b, c) {
  switch(typeof b) {
    case "string":
      gc(b, c);
      break;
    case "number":
      c.push(isFinite(b) && !isNaN(b) ? b : "null");
      break;
    case "boolean":
      c.push(b);
      break;
    case "undefined":
      c.push("null");
      break;
    case "object":
      if(b == k) {
        c.push("null");
        break
      }
      if(ga(b)) {
        var d = b.length;
        c.push("[");
        for(var g = "", f = 0;f < d;f++) {
          c.push(g), g = b[f], ec(a, a.$b ? a.$b.call(b, String(f), g) : g, c), g = ","
        }
        c.push("]");
        break
      }
      c.push("{");
      d = "";
      for(f in b) {
        Object.prototype.hasOwnProperty.call(b, f) && (g = b[f], "function" != typeof g && (c.push(d), gc(f, c), c.push(":"), ec(a, a.$b ? a.$b.call(b, f, g) : g, c), d = ","))
      }
      c.push("}");
      break;
    case "function":
      break;
    default:
      e(Error("Unknown type: " + typeof b))
  }
}
var hc = {'"':'\\"', "\\":"\\\\", "/":"\\/", "\b":"\\b", "\f":"\\f", "\n":"\\n", "\r":"\\r", "\t":"\\t", "\x0B":"\\u000b"}, ic = /\uffff/.test("\uffff") ? /[\\\"\x00-\x1f\x7f-\uffff]/g : /[\\\"\x00-\x1f\x7f-\xff]/g;
function gc(a, b) {
  b.push('"', a.replace(ic, function(a) {
    if(a in hc) {
      return hc[a]
    }
    var b = a.charCodeAt(0), g = "\\u";
    16 > b ? g += "000" : 256 > b ? g += "00" : 4096 > b && (g += "0");
    return hc[a] = g + b.toString(16)
  }), '"')
}
;function jc(a, b, c) {
  var d = gb(c, a);
  if(-1 != d) {
    b.push("#CYCLETO:" + (c.length - d) + "#")
  }else {
    c.push(a);
    d = fa(a);
    if("boolean" == d || "number" == d || "null" == d || "undefined" == d) {
      b.push(String(a))
    }else {
      if("string" == d) {
        gc(a, b)
      }else {
        if(cc(a.B)) {
          a.B(b, c)
        }else {
          if(cc(a.Le)) {
            b.push("<cw.eq.Wildcard>")
          }else {
            if(a instanceof RegExp) {
              b.push(a.toString())
            }else {
              if("array" == d) {
                d = a.length;
                b.push("[");
                for(var g = "", f = 0;f < d;f++) {
                  b.push(g), jc(a[f], b, c), g = ", "
                }
                b.push("]")
              }else {
                if("object" == d) {
                  if(ia(a) && "function" == typeof a.valueOf) {
                    b.push("new Date(", String(a.valueOf()), ")")
                  }else {
                    for(var d = ab(a).concat(bb), g = {}, i = f = 0;i < d.length;) {
                      var l = d[i++], n = ja(l) ? "o" + B(l) : (typeof l).charAt(0) + l;
                      Object.prototype.hasOwnProperty.call(g, n) || (g[n] = j, d[f++] = l)
                    }
                    d.length = f;
                    b.push("{");
                    g = "";
                    for(i = 0;i < d.length;i++) {
                      f = d[i], Object.prototype.hasOwnProperty.call(a, f) && (l = a[f], b.push(g), gc(f, b), b.push(": "), jc(l, b, c), g = ", ")
                    }
                    b.push("}")
                  }
                }else {
                  b.push(a.toString())
                }
              }
            }
          }
        }
      }
    }
    c.pop()
  }
}
function O(a, b, c) {
  c || (c = []);
  jc(a, b, c)
}
function P(a) {
  var b = [];
  O(a, b, h);
  return b.join("")
}
;function kc() {
  var a = Math.pow(10, 9);
  return a + Math.random() * (Math.pow(10, 10) - a)
}
;function lc(a, b) {
  this.x = w(a) ? a : 0;
  this.y = w(b) ? b : 0
}
lc.prototype.L = function() {
  return new lc(this.x, this.y)
};
lc.prototype.toString = function() {
  return"(" + this.x + ", " + this.y + ")"
};
function mc(a, b) {
  this.width = a;
  this.height = b
}
t = mc.prototype;
t.L = function() {
  return new mc(this.width, this.height)
};
t.toString = function() {
  return"(" + this.width + " x " + this.height + ")"
};
t.Ra = function() {
  return!(this.width * this.height)
};
t.floor = function() {
  this.width = Math.floor(this.width);
  this.height = Math.floor(this.height);
  return this
};
t.round = function() {
  this.width = Math.round(this.width);
  this.height = Math.round(this.height);
  return this
};
var nc;
function oc(a) {
  a = a.className;
  return x(a) && a.match(/\S+/g) || []
}
function pc(a, b) {
  for(var c = oc(a), d = qb(arguments, 1), g = c.length + d.length, f = c, i = 0;i < d.length;i++) {
    mb(f, d[i]) || f.push(d[i])
  }
  a.className = c.join(" ");
  return c.length == g
}
function qc(a, b) {
  var c = oc(a), d = qb(arguments, 1), g, f = d;
  g = ib(c, function(a) {
    return!mb(f, a)
  });
  a.className = g.join(" ");
  return g.length == c.length - d.length
}
;var rc = !G || Wa(9), sc = !H && !G || G && Wa(9) || H && J("1.9.1"), tc = G && !J("9");
function uc(a) {
  return a ? new vc(wc(a)) : nc || (nc = new vc)
}
function Q(a) {
  return x(a) ? document.getElementById(a) : a
}
var xc = {cellpadding:"cellPadding", cellspacing:"cellSpacing", colspan:"colSpan", frameborder:"frameBorder", height:"height", maxlength:"maxLength", role:"role", rowspan:"rowSpan", type:"type", usemap:"useMap", valign:"vAlign", width:"width"};
function yc(a) {
  var b = !I && "CSS1Compat" == a.compatMode ? a.documentElement : a.body, a = a.parentWindow || a.defaultView;
  return new lc(a.pageXOffset || b.scrollLeft, a.pageYOffset || b.scrollTop)
}
function zc(a, b, c) {
  return Ac(document, arguments)
}
function Ac(a, b) {
  var c = b[0], d = b[1];
  if(!rc && d && (d.name || d.type)) {
    c = ["<", c];
    d.name && c.push(' name="', sa(d.name), '"');
    if(d.type) {
      c.push(' type="', sa(d.type), '"');
      var g = {};
      cb(g, d);
      delete g.type;
      d = g
    }
    c.push(">");
    c = c.join("")
  }
  var f = a.createElement(c);
  d && (x(d) ? f.className = d : ga(d) ? pc.apply(k, [f].concat(d)) : Za(d, function(a, b) {
    "style" == b ? f.style.cssText = a : "class" == b ? f.className = a : "for" == b ? f.htmlFor = a : b in xc ? f.setAttribute(xc[b], a) : 0 == b.lastIndexOf("aria-", 0) || 0 == b.lastIndexOf("data-", 0) ? f.setAttribute(b, a) : f[b] = a
  }));
  2 < b.length && Bc(a, f, b, 2);
  return f
}
function Bc(a, b, c, d) {
  function g(c) {
    c && b.appendChild(x(c) ? a.createTextNode(c) : c)
  }
  for(;d < c.length;d++) {
    var f = c[d];
    if(ha(f) && !(ja(f) && 0 < f.nodeType)) {
      var i = hb, l;
      a: {
        if((l = f) && "number" == typeof l.length) {
          if(ja(l)) {
            l = "function" == typeof l.item || "string" == typeof l.item;
            break a
          }
          if(z(l)) {
            l = "function" == typeof l.item;
            break a
          }
        }
        l = m
      }
      i(l ? pb(f) : f, g)
    }else {
      g(f)
    }
  }
}
function Cc(a, b) {
  Bc(wc(a), a, arguments, 1)
}
function Dc(a, b) {
  if(a.contains && 1 == b.nodeType) {
    return a == b || a.contains(b)
  }
  if("undefined" != typeof a.compareDocumentPosition) {
    return a == b || Boolean(a.compareDocumentPosition(b) & 16)
  }
  for(;b && a != b;) {
    b = b.parentNode
  }
  return b == a
}
function wc(a) {
  return 9 == a.nodeType ? a : a.ownerDocument || a.document
}
var Ec = {SCRIPT:1, STYLE:1, HEAD:1, IFRAME:1, OBJECT:1}, Gc = {IMG:" ", BR:"\n"};
function Hc(a) {
  var b = a.getAttributeNode("tabindex");
  return b && b.specified ? (a = a.tabIndex, "number" == typeof a && 0 <= a && 32768 > a) : m
}
function Ic(a) {
  var b = [];
  Jc(a, b, m);
  return b.join("")
}
function Jc(a, b, c) {
  if(!(a.nodeName in Ec)) {
    if(3 == a.nodeType) {
      c ? b.push(String(a.nodeValue).replace(/(\r\n|\r|\n)/g, "")) : b.push(a.nodeValue)
    }else {
      if(a.nodeName in Gc) {
        b.push(Gc[a.nodeName])
      }else {
        for(a = a.firstChild;a;) {
          Jc(a, b, c), a = a.nextSibling
        }
      }
    }
  }
}
function vc(a) {
  this.M = a || u.document || document
}
t = vc.prototype;
t.Na = uc;
t.k = function(a) {
  return x(a) ? this.M.getElementById(a) : a
};
function Kc(a, b) {
  var c;
  c = a.M;
  var d = b && "*" != b ? b.toUpperCase() : "";
  c = c.querySelectorAll && c.querySelector && d ? c.querySelectorAll(d + "") : c.getElementsByTagName(d || "*");
  return c
}
t.z = function(a, b, c) {
  return Ac(this.M, arguments)
};
t.createElement = function(a) {
  return this.M.createElement(a)
};
t.createTextNode = function(a) {
  return this.M.createTextNode(a)
};
t.appendChild = function(a, b) {
  a.appendChild(b)
};
t.append = Cc;
t.Ed = function(a) {
  return sc && a.children != h ? a.children : ib(a.childNodes, function(a) {
    return 1 == a.nodeType
  })
};
t.contains = Dc;
function Lc(a, b) {
  var c;
  a: {
    c = wc(a);
    if(c.defaultView && c.defaultView.getComputedStyle && (c = c.defaultView.getComputedStyle(a, k))) {
      c = c[b] || c.getPropertyValue(b) || "";
      break a
    }
    c = ""
  }
  return c || (a.currentStyle ? a.currentStyle[b] : k) || a.style && a.style[b]
}
function Mc(a) {
  if(G && !Wa(8)) {
    return a.offsetParent
  }
  for(var b = wc(a), c = Lc(a, "position"), d = "fixed" == c || "absolute" == c, a = a.parentNode;a && a != b;a = a.parentNode) {
    if(c = Lc(a, "position"), d = d && "static" == c && a != b.documentElement && a != b.body, !d && (a.scrollWidth > a.clientWidth || a.scrollHeight > a.clientHeight || "fixed" == c || "absolute" == c || "relative" == c)) {
      return a
    }
  }
  return k
}
function Nc(a) {
  "number" == typeof a && (a = Math.round(a) + "px");
  return a
}
function Oc(a) {
  G ? a.cssText = ".dbg-sev{color:#F00}.dbg-w{color:#C40}.dbg-sh{font-weight:bold;color:#000}.dbg-i{color:#444}.dbg-f{color:#999}.dbg-ev{color:#0A0}.dbg-m{color:#990}.logmsg{border-bottom:1px solid #CCC;padding:2px}.logsep{background-color: #8C8;}.logdiv{border:1px solid #CCC;background-color:#FCFCFC;font:medium monospace}" : a.innerHTML = ".dbg-sev{color:#F00}.dbg-w{color:#C40}.dbg-sh{font-weight:bold;color:#000}.dbg-i{color:#444}.dbg-f{color:#999}.dbg-ev{color:#0A0}.dbg-m{color:#990}.logmsg{border-bottom:1px solid #CCC;padding:2px}.logsep{background-color: #8C8;}.logdiv{border:1px solid #CCC;background-color:#FCFCFC;font:medium monospace}"
}
var Pc = H ? "MozUserSelect" : I ? "WebkitUserSelect" : k;
function Qc(a) {
  L.call(this);
  this.Od = a;
  this.j = []
}
E(Qc, L);
var Rc = [];
function R(a, b, c, d) {
  ga(c) || (Rc[0] = c, c = Rc);
  for(var g = 0;g < c.length;g++) {
    var f = N(b, c[g], d || a, m, a.Od || a);
    a.j.push(f)
  }
  return a
}
function Sc(a, b, c, d, g, f) {
  if(ga(c)) {
    for(var i = 0;i < c.length;i++) {
      Sc(a, b, c[i], d, g, f)
    }
  }else {
    a: {
      d = d || a;
      f = f || a.Od || a;
      g = !!g;
      if(b = Ib(b, c, g)) {
        for(c = 0;c < b.length;c++) {
          if(!b[c].Ia && b[c].Wa == d && b[c].capture == g && b[c].Ob == f) {
            b = b[c];
            break a
          }
        }
      }
      b = k
    }
    b && (b = b.key, Jb(b), nb(a.j, b))
  }
  return a
}
Qc.prototype.Wc = function() {
  hb(this.j, Jb);
  this.j.length = 0
};
Qc.prototype.c = function() {
  Qc.g.c.call(this);
  this.Wc()
};
Qc.prototype.handleEvent = function() {
  e(Error("EventHandler.handleEvent not implemented"))
};
function Tc() {
}
ea(Tc);
Tc.prototype.sf = 0;
Tc.Oa();
function Uc(a) {
  L.call(this);
  this.Eb = a || uc();
  this.tb = Vc
}
E(Uc, Ob);
Uc.prototype.kf = Tc.Oa();
var Vc = k;
function Wc(a, b) {
  switch(a) {
    case 1:
      return b ? "disable" : "enable";
    case 2:
      return b ? "highlight" : "unhighlight";
    case 4:
      return b ? "activate" : "deactivate";
    case 8:
      return b ? "select" : "unselect";
    case 16:
      return b ? "check" : "uncheck";
    case 32:
      return b ? "focus" : "blur";
    case 64:
      return b ? "open" : "close"
  }
  e(Error("Invalid component state"))
}
t = Uc.prototype;
t.W = k;
t.T = m;
t.f = k;
t.tb = k;
t.qf = k;
t.t = k;
t.ia = k;
t.Cb = k;
t.Of = m;
function Xc(a) {
  return a.W || (a.W = ":" + (a.kf.sf++).toString(36))
}
t.k = p("f");
function Yc(a) {
  return a.Pa || (a.Pa = new Qc(a))
}
t.getParent = p("t");
t.Zc = function(a) {
  this.t && this.t != a && e(Error("Method not supported"));
  Uc.g.Zc.call(this, a)
};
t.Na = p("Eb");
t.z = function() {
  this.f = this.Eb.createElement("div")
};
function Zc(a, b) {
  a.T && e(Error("Component already rendered"));
  a.f || a.z();
  b ? b.insertBefore(a.f, k) : a.Eb.M.body.appendChild(a.f);
  (!a.t || a.t.T) && a.la()
}
t.la = function() {
  this.T = j;
  $c(this, function(a) {
    !a.T && a.k() && a.la()
  })
};
t.hb = function() {
  $c(this, function(a) {
    a.T && a.hb()
  });
  this.Pa && this.Pa.Wc();
  this.T = m
};
t.c = function() {
  Uc.g.c.call(this);
  this.T && this.hb();
  this.Pa && (this.Pa.b(), delete this.Pa);
  $c(this, function(a) {
    a.b()
  });
  if(!this.Of && this.f) {
    var a = this.f;
    a && a.parentNode && a.parentNode.removeChild(a)
  }
  this.t = this.qf = this.f = this.Cb = this.ia = k
};
t.$a = function(a) {
  this.T && e(Error("Component already rendered"));
  this.tb = a
};
function $c(a, b) {
  a.ia && hb(a.ia, b, h)
}
t.removeChild = function(a, b) {
  if(a) {
    var c = x(a) ? a : Xc(a), d;
    this.Cb && c ? (d = this.Cb, d = (c in d ? d[c] : h) || k) : d = k;
    a = d;
    c && a && (d = this.Cb, c in d && delete d[c], nb(this.ia, a), b && (a.hb(), a.f && (c = a.f) && c.parentNode && c.parentNode.removeChild(c)), c = a, c == k && e(Error("Unable to set parent component")), c.t = k, Uc.g.Zc.call(c, k))
  }
  a || e(Error("Child is not in parent component"));
  return a
};
function ad() {
  this.re = pa()
}
var bd = new ad;
ad.prototype.set = ba("re");
ad.prototype.reset = function() {
  this.set(pa())
};
ad.prototype.get = p("re");
function cd(a) {
  this.vf = a || "";
  this.Df = bd
}
cd.prototype.ye = j;
cd.prototype.Cf = j;
cd.prototype.Bf = j;
cd.prototype.ze = m;
function dd(a) {
  return 10 > a ? "0" + a : String(a)
}
function ed(a, b) {
  var c = (a.Ee - b) / 1E3, d = c.toFixed(3), g = 0;
  if(1 > c) {
    g = 2
  }else {
    for(;100 > c;) {
      g++, c *= 10
    }
  }
  for(;0 < g--;) {
    d = " " + d
  }
  return d
}
function fd(a) {
  cd.call(this, a)
}
E(fd, cd);
fd.prototype.ze = j;
function gd(a) {
  if("function" == typeof a.F) {
    a = a.F()
  }else {
    if(ha(a) || x(a)) {
      a = a.length
    }else {
      var b = 0, c;
      for(c in a) {
        b++
      }
      a = b
    }
  }
  return a
}
function hd(a) {
  if("function" == typeof a.C) {
    return a.C()
  }
  if(x(a)) {
    return a.split("")
  }
  if(ha(a)) {
    for(var b = [], c = a.length, d = 0;d < c;d++) {
      b.push(a[d])
    }
    return b
  }
  return $a(a)
}
function id(a) {
  if("function" == typeof a.ba) {
    return a.ba()
  }
  if("function" != typeof a.C) {
    if(ha(a) || x(a)) {
      for(var b = [], a = a.length, c = 0;c < a;c++) {
        b.push(c)
      }
      return b
    }
    return ab(a)
  }
}
function jd(a, b, c) {
  if("function" == typeof a.forEach) {
    a.forEach(b, c)
  }else {
    if(ha(a) || x(a)) {
      hb(a, b, c)
    }else {
      for(var d = id(a), g = hd(a), f = g.length, i = 0;i < f;i++) {
        b.call(c, g[i], d && d[i], a)
      }
    }
  }
}
function kd(a, b) {
  if("function" == typeof a.every) {
    return a.every(b, h)
  }
  if(ha(a) || x(a)) {
    return lb(a, b, h)
  }
  for(var c = id(a), d = hd(a), g = d.length, f = 0;f < g;f++) {
    if(!b.call(h, d[f], c && c[f], a)) {
      return m
    }
  }
  return j
}
;function ld(a, b) {
  this.o = {};
  this.j = [];
  var c = arguments.length;
  if(1 < c) {
    c % 2 && e(Error("Uneven number of arguments"));
    for(var d = 0;d < c;d += 2) {
      this.set(arguments[d], arguments[d + 1])
    }
  }else {
    a && this.mc(a)
  }
}
t = ld.prototype;
t.d = 0;
t.md = 0;
t.F = p("d");
t.C = function() {
  md(this);
  for(var a = [], b = 0;b < this.j.length;b++) {
    a.push(this.o[this.j[b]])
  }
  return a
};
t.ba = function() {
  md(this);
  return this.j.concat()
};
t.ja = function(a) {
  return nd(this.o, a)
};
t.uc = function(a) {
  for(var b = 0;b < this.j.length;b++) {
    var c = this.j[b];
    if(nd(this.o, c) && this.o[c] == a) {
      return j
    }
  }
  return m
};
t.O = function(a, b) {
  if(this === a) {
    return j
  }
  if(this.d != a.F()) {
    return m
  }
  var c = b || od;
  md(this);
  for(var d, g = 0;d = this.j[g];g++) {
    if(!c(this.get(d), a.get(d))) {
      return m
    }
  }
  return j
};
function od(a, b) {
  return a === b
}
t.Ra = function() {
  return 0 == this.d
};
t.clear = function() {
  this.o = {};
  this.md = this.d = this.j.length = 0
};
t.remove = function(a) {
  return nd(this.o, a) ? (delete this.o[a], this.d--, this.md++, this.j.length > 2 * this.d && md(this), j) : m
};
function md(a) {
  if(a.d != a.j.length) {
    for(var b = 0, c = 0;b < a.j.length;) {
      var d = a.j[b];
      nd(a.o, d) && (a.j[c++] = d);
      b++
    }
    a.j.length = c
  }
  if(a.d != a.j.length) {
    for(var g = {}, c = b = 0;b < a.j.length;) {
      d = a.j[b], nd(g, d) || (a.j[c++] = d, g[d] = 1), b++
    }
    a.j.length = c
  }
}
t.get = function(a, b) {
  return nd(this.o, a) ? this.o[a] : b
};
t.set = function(a, b) {
  nd(this.o, a) || (this.d++, this.j.push(a), this.md++);
  this.o[a] = b
};
t.mc = function(a) {
  var b;
  a instanceof ld ? (b = a.ba(), a = a.C()) : (b = ab(a), a = $a(a));
  for(var c = 0;c < b.length;c++) {
    this.set(b[c], a[c])
  }
};
t.L = function() {
  return new ld(this)
};
function pd(a) {
  md(a);
  for(var b = {}, c = 0;c < a.j.length;c++) {
    var d = a.j[c];
    b[d] = a.o[d]
  }
  return b
}
function nd(a, b) {
  return Object.prototype.hasOwnProperty.call(a, b)
}
;function qd(a) {
  this.o = new ld;
  a && this.mc(a)
}
function rd(a) {
  var b = typeof a;
  return"object" == b && a || "function" == b ? "o" + B(a) : b.substr(0, 1) + a
}
t = qd.prototype;
t.F = function() {
  return this.o.F()
};
t.add = function(a) {
  this.o.set(rd(a), a)
};
t.mc = function(a) {
  for(var a = hd(a), b = a.length, c = 0;c < b;c++) {
    this.add(a[c])
  }
};
t.Wc = function(a) {
  for(var a = hd(a), b = a.length, c = 0;c < b;c++) {
    this.remove(a[c])
  }
};
t.remove = function(a) {
  return this.o.remove(rd(a))
};
t.clear = function() {
  this.o.clear()
};
t.Ra = function() {
  return this.o.Ra()
};
t.contains = function(a) {
  return this.o.ja(rd(a))
};
t.C = function() {
  return this.o.C()
};
t.L = function() {
  return new qd(this)
};
t.O = function(a) {
  var b;
  if(b = this.F() == gd(a)) {
    var c = a, a = gd(c);
    this.F() > a ? b = m : (!(c instanceof qd) && 5 < a && (c = new qd(c)), b = kd(this, function(a) {
      if("function" == typeof c.contains) {
        a = c.contains(a)
      }else {
        if("function" == typeof c.uc) {
          a = c.uc(a)
        }else {
          if(ha(c) || x(c)) {
            a = mb(c, a)
          }else {
            a: {
              for(var b in c) {
                if(c[b] == a) {
                  a = j;
                  break a
                }
              }
              a = m
            }
          }
        }
      }
      return a
    }))
  }
  return b
};
function sd(a) {
  return td(a || arguments.callee.caller, [])
}
function td(a, b) {
  var c = [];
  if(mb(b, a)) {
    c.push("[...circular reference...]")
  }else {
    if(a && 50 > b.length) {
      c.push(ud(a) + "(");
      for(var d = a.arguments, g = 0;g < d.length;g++) {
        0 < g && c.push(", ");
        var f;
        f = d[g];
        switch(typeof f) {
          case "object":
            f = f ? "object" : "null";
            break;
          case "string":
            break;
          case "number":
            f = String(f);
            break;
          case "boolean":
            f = f ? "true" : "false";
            break;
          case "function":
            f = (f = ud(f)) ? f : "[fn]";
            break;
          default:
            f = typeof f
        }
        40 < f.length && (f = f.substr(0, 40) + "...");
        c.push(f)
      }
      b.push(a);
      c.push(")\n");
      try {
        c.push(td(a.caller, b))
      }catch(i) {
        c.push("[exception trying to get caller]\n")
      }
    }else {
      a ? c.push("[...long stack...]") : c.push("[end]")
    }
  }
  return c.join("")
}
function ud(a) {
  if(vd[a]) {
    return vd[a]
  }
  a = String(a);
  if(!vd[a]) {
    var b = /function ([^\(]+)/.exec(a);
    vd[a] = b ? b[1] : "[Anonymous]"
  }
  return vd[a]
}
var vd = {};
function wd(a, b, c, d, g) {
  this.reset(a, b, c, d, g)
}
wd.prototype.Af = 0;
wd.prototype.Bc = k;
wd.prototype.Ac = k;
var xd = 0;
wd.prototype.reset = function(a, b, c, d, g) {
  this.Af = "number" == typeof g ? g : xd++;
  this.Ee = d || pa();
  this.Va = a;
  this.fe = b;
  this.mf = c;
  delete this.Bc;
  delete this.Ac
};
wd.prototype.dc = ba("Va");
function yd(a) {
  this.rf = a
}
yd.prototype.t = k;
yd.prototype.Va = k;
yd.prototype.ia = k;
yd.prototype.lb = k;
function zd(a, b) {
  this.name = a;
  this.value = b
}
zd.prototype.toString = p("name");
var Ad = new zd("OFF", Infinity), Bd = new zd("SHOUT", 1200), Cd = new zd("SEVERE", 1E3), Dd = new zd("WARNING", 900), Ed = new zd("INFO", 800), Fd = new zd("CONFIG", 700), Gd = new zd("FINE", 500), Hd = new zd("FINEST", 300), Id = new zd("ALL", 0);
t = yd.prototype;
t.getParent = p("t");
t.Ed = function() {
  this.ia || (this.ia = {});
  return this.ia
};
t.dc = ba("Va");
function Jd(a) {
  if(a.Va) {
    return a.Va
  }
  if(a.t) {
    return Jd(a.t)
  }
  Ba("Root logger has no level set.");
  return k
}
t.log = function(a, b, c) {
  if(a.value >= Jd(this).value) {
    a = this.df(a, b, c);
    b = "log:" + a.fe;
    u.console && (u.console.timeStamp ? u.console.timeStamp(b) : u.console.markTimeline && u.console.markTimeline(b));
    u.msWriteProfilerMark && u.msWriteProfilerMark(b);
    for(b = this;b;) {
      var c = b, d = a;
      if(c.lb) {
        for(var g = 0, f = h;f = c.lb[g];g++) {
          f(d)
        }
      }
      b = b.getParent()
    }
  }
};
t.df = function(a, b, c) {
  var d = new wd(a, String(b), this.rf);
  if(c) {
    d.Bc = c;
    var g;
    var f = arguments.callee.caller;
    try {
      var i;
      var l = da("window.location.href");
      if(x(c)) {
        i = {message:c, name:"Unknown error", lineNumber:"Not available", fileName:l, stack:"Not available"}
      }else {
        var n, s, A = m;
        try {
          n = c.lineNumber || c.Zg || "Not available"
        }catch(r) {
          n = "Not available", A = j
        }
        try {
          s = c.fileName || c.filename || c.sourceURL || l
        }catch(y) {
          s = "Not available", A = j
        }
        i = A || !c.lineNumber || !c.fileName || !c.stack ? {message:c.message, name:c.name, lineNumber:n, fileName:s, stack:c.stack || "Not available"} : c
      }
      g = "Message: " + sa(i.message) + '\nUrl: <a href="view-source:' + i.fileName + '" target="_new">' + i.fileName + "</a>\nLine: " + i.lineNumber + "\n\nBrowser stack:\n" + sa(i.stack + "-> ") + "[end]\n\nJS stack traversal:\n" + sa(sd(f) + "-> ")
    }catch(D) {
      g = "Exception trying to expose exception! You win, we lose. " + D
    }
    d.Ac = g
  }
  return d
};
function S(a, b) {
  a.log(Cd, b, h)
}
function T(a, b, c) {
  a.log(Dd, b, c)
}
t.info = function(a, b) {
  this.log(Ed, a, b)
};
function U(a, b) {
  a.log(Gd, b, h)
}
function V(a, b) {
  a.log(Hd, b, h)
}
var Kd = {}, Ld = k;
function Md() {
  Ld || (Ld = new yd(""), Kd[""] = Ld, Ld.dc(Fd))
}
function Nd() {
  Md();
  return Ld
}
function W(a) {
  Md();
  var b;
  if(!(b = Kd[a])) {
    b = new yd(a);
    var c = a.lastIndexOf("."), d = a.substr(c + 1), c = W(a.substr(0, c));
    c.Ed()[d] = b;
    b.t = c;
    Kd[a] = b
  }
  return b
}
;function Od(a) {
  this.wf = C(this.Me, this);
  this.Dd = new fd;
  this.Vd = this.Dd.ye = m;
  this.f = a;
  this.Ze = this.f.ownerDocument || this.f.document;
  var a = uc(this.f), b = k;
  if(G) {
    b = a.M.createStyleSheet(), Oc(b)
  }else {
    var c = Kc(a, "head")[0];
    c || (b = Kc(a, "body")[0], c = a.z("head"), b.parentNode.insertBefore(c, b));
    b = a.z("style");
    Oc(b);
    a.appendChild(c, b)
  }
  this.f.className += " logdiv"
}
Od.prototype.Me = function(a) {
  var b = 100 >= this.f.scrollHeight - this.f.scrollTop - this.f.clientHeight, c = this.Ze.createElement("div");
  c.className = "logmsg";
  var d = this.Dd, g;
  switch(a.Va.value) {
    case Bd.value:
      g = "dbg-sh";
      break;
    case Cd.value:
      g = "dbg-sev";
      break;
    case Dd.value:
      g = "dbg-w";
      break;
    case Ed.value:
      g = "dbg-i";
      break;
    default:
      g = "dbg-f"
  }
  var f = [];
  f.push(d.vf, " ");
  if(d.ye) {
    var i = new Date(a.Ee);
    f.push("[", dd(i.getFullYear() - 2E3) + dd(i.getMonth() + 1) + dd(i.getDate()) + " " + dd(i.getHours()) + ":" + dd(i.getMinutes()) + ":" + dd(i.getSeconds()) + "." + dd(Math.floor(i.getMilliseconds() / 10)), "] ")
  }
  d.Cf && f.push("[", ya(ed(a, d.Df.get())), "s] ");
  d.Bf && f.push("[", sa(a.mf), "] ");
  f.push('<span class="', g, '">', ra(ya(sa(a.fe))));
  d.ze && a.Bc && f.push("<br>", ra(ya(a.Ac || "")));
  f.push("</span><br>");
  c.innerHTML = f.join("");
  this.f.appendChild(c);
  b && (this.f.scrollTop = this.f.scrollHeight)
};
Od.prototype.clear = function() {
  this.f.innerHTML = ""
};
function Pd(a) {
  var b = fa(a);
  if("string" == b) {
    return 21 + 2 * a.length
  }
  if("number" == b) {
    return 16
  }
  if("boolean" == b) {
    return 12
  }
  if("null" == b || "undefined" == b) {
    return 8
  }
  e(Error("cannot determine size of object type " + b))
}
;var Qd, Rd;
function Sd(a, b) {
  this.La = a;
  this.Ja = b
}
Sd.prototype.O = function(a) {
  return a instanceof Sd && this.La == a.La && this.Ja.join(",") == a.Ja
};
Sd.prototype.B = function(a, b) {
  a.push("new SACK(", String(this.La), ", ");
  O(this.Ja, a, b);
  a.push(")")
};
function Td() {
  this.G = new ld
}
Td.prototype.Ca = -1;
Td.prototype.J = 0;
Td.prototype.append = function(a) {
  var b = Pd(a);
  this.G.set(this.Ca + 1, [a, b]);
  this.Ca += 1;
  this.J += b
};
Td.prototype.B = function(a) {
  a.push("<Queue with ", String(this.G.F()), " item(s), counter=#", String(this.Ca), ", size=", String(this.J), ">")
};
function Ud(a) {
  a = a.G.ba();
  K.sort.call(a, rb);
  return a
}
function Vd() {
  this.Aa = new ld
}
Vd.prototype.Fa = -1;
Vd.prototype.J = 0;
function Xd(a) {
  var b = a.Aa.ba();
  K.sort.call(b, rb);
  return new Sd(a.Fa, b)
}
var Yd = {};
function Zd(a, b) {
  switch(fa(b)) {
    case "string":
      a.push("<string>", sa(b), "</string>");
      break;
    case "number":
      a.push("<number>", b, "</number>");
      break;
    case "boolean":
      a.push(b ? "<true/>" : "<false/>");
      break;
    case "undefined":
      a.push("<undefined/>");
      break;
    case "array":
      a.push("<array>");
      for(var c = b.length, d = 0;d < c;d++) {
        a.push('<property id="', d, '">'), Zd(a, b[d]), a.push("</property>")
      }
      a.push("</array>");
      break;
    case "object":
      if("function" == typeof b.getFullYear) {
        a.push("<date>", b.valueOf(), "</date>")
      }else {
        a.push("<object>");
        for(c in b) {
          Object.prototype.hasOwnProperty.call(b, c) && "function" != fa(b[c]) && (a.push('<property id="', sa(c), '">'), Zd(a, b[c]), a.push("</property>"))
        }
        a.push("</object>")
      }
      break;
    default:
      a.push("<null/>")
  }
}
function $d(a, b) {
  var c = ['<invoke name="', a, '" returntype="javascript">'], d = c, g = arguments;
  d.push("<arguments>");
  for(var f = g.length, i = 1;i < f;i++) {
    Zd(d, g[i])
  }
  d.push("</arguments>");
  c.push("</invoke>");
  return c.join("")
}
;var ae = m, be = "";
function ce(a) {
  a = a.match(/[\d]+/g);
  a.length = 3;
  return a.join(".")
}
if(navigator.plugins && navigator.plugins.length) {
  var de = navigator.plugins["Shockwave Flash"];
  de && (ae = j, de.description && (be = ce(de.description)));
  navigator.plugins["Shockwave Flash 2.0"] && (ae = j, be = "2.0.0.11")
}else {
  if(navigator.mimeTypes && navigator.mimeTypes.length) {
    var ee = navigator.mimeTypes["application/x-shockwave-flash"];
    (ae = ee && ee.enabledPlugin) && (be = ce(ee.enabledPlugin.description))
  }else {
    try {
      var fe = new ActiveXObject("ShockwaveFlash.ShockwaveFlash.7"), ae = j, be = ce(fe.GetVariable("$version"))
    }catch(ge) {
      try {
        fe = new ActiveXObject("ShockwaveFlash.ShockwaveFlash.6"), ae = j, be = "6.0.21"
      }catch(he) {
        try {
          fe = new ActiveXObject("ShockwaveFlash.ShockwaveFlash"), ae = j, be = ce(fe.GetVariable("$version"))
        }catch(ie) {
        }
      }
    }
  }
}
var je = be;
function ke(a, b) {
  Uc.call(this, b);
  this.bf = a;
  this.zc = new Qc(this);
  this.Hb = new ld
}
E(ke, Uc);
t = ke.prototype;
t.a = W("goog.ui.media.FlashObject");
t.Qf = "window";
t.pd = "#000000";
t.Ne = "sameDomain";
function le(a, b, c) {
  a.nd = x(b) ? b : Math.round(b) + "px";
  a.Fc = x(c) ? c : Math.round(c) + "px";
  a.k() && (b = a.k() ? a.k().firstChild : k, c = a.nd, a = a.Fc, c instanceof mc ? (a = c.height, c = c.width) : a == h && e(Error("missing height argument")), b.style.width = Nc(c), b.style.height = Nc(a))
}
t.la = function() {
  ke.g.la.call(this);
  var a = this.k(), b;
  b = G ? '<object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000" id="%s" name="%s" class="%s"><param name="movie" value="%s"/><param name="quality" value="high"/><param name="FlashVars" value="%s"/><param name="bgcolor" value="%s"/><param name="AllowScriptAccess" value="%s"/><param name="allowFullScreen" value="true"/><param name="SeamlessTabbing" value="false"/>%s</object>' : '<embed quality="high" id="%s" name="%s" class="%s" src="%s" FlashVars="%s" bgcolor="%s" AllowScriptAccess="%s" allowFullScreen="true" SeamlessTabbing="false" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/go/getflashplayer" %s></embed>';
  for(var c = G ? '<param name="wmode" value="%s"/>' : "wmode=%s", c = qa(c, this.Qf), d = this.Hb.ba(), g = this.Hb.C(), f = [], i = 0;i < d.length;i++) {
    f.push(encodeURIComponent(String(d[i])) + "=" + encodeURIComponent(String(g[i])))
  }
  b = qa(b, Xc(this), Xc(this), "goog-ui-media-flash-object", sa(this.bf), sa(f.join("&")), this.pd, this.Ne, c);
  a.innerHTML = b;
  this.nd && this.Fc && le(this, this.nd, this.Fc);
  R(this.zc, this.k(), $a(sb), xb)
};
t.z = function() {
  this.te != k && !(0 <= za(je, this.te)) && (T(this.a, "Required flash version not found:" + this.te), e(Error("Method not supported")));
  var a = this.Na().createElement("div");
  a.className = "goog-ui-media-flash";
  this.f = a
};
t.c = function() {
  ke.g.c.call(this);
  this.Hb = k;
  this.zc.b();
  this.zc = k
};
function me() {
  return Math.floor(2147483648 * Math.random()).toString(36) + Math.abs(Math.floor(2147483648 * Math.random()) ^ pa()).toString(36)
}
function ne(a) {
  return a.substr(0, a.length - 1)
}
var oe = /^(0|[1-9]\d*)$/, pe = /^(0|\-?[1-9]\d*)$/;
function qe(a) {
  var b = re;
  return oe.test(a) && (a = parseInt(a, 10), a <= b) ? a : k
}
;function se(a) {
  F.call(this, a)
}
E(se, F);
se.prototype.name = "cw.loadflash.FlashLoadFailed";
u.__loadFlashObject_callbacks = {};
function te(a, b) {
  L.call(this);
  this.W = "_" + me();
  this.ic = a;
  this.ta = b;
  this.za = a.za
}
E(te, L);
t = te.prototype;
t.Ga = j;
t.Db = m;
t.a = W("cw.net.FlashSocket");
t.B = function(a) {
  a.push("<FlashSocket id='");
  a.push(this.W);
  a.push("'>")
};
function ue(a, b, c) {
  if("frames" == b) {
    a = a.ta, ve(a.A), we(a.A, c)
  }else {
    if("stillreceiving" == b) {
      c = a.ta, V(c.a, "onstillreceiving"), ve(c.A)
    }else {
      if("connect" == b) {
        a.ta.onconnect()
      }else {
        "close" == b ? (a.Ga = m, a.b()) : "ioerror" == b ? (a.Ga = m, b = a.ta, T(b.a, "onioerror: " + P(c)), xe(b.A, m), a.b()) : "securityerror" == b ? (a.Ga = m, b = a.ta, T(b.a, "onsecurityerror: " + P(c)), xe(b.A, m), a.b()) : e(Error("bad event: " + b))
      }
    }
  }
}
t.tc = function(a, b) {
  try {
    var c = this.za.CallFunction($d("__FC_connect", this.W, a, b, "<int32/>\n"))
  }catch(d) {
    S(this.a, "connect: could not call __FC_connect; Flash probably crashed. Disposing now. Error was: " + d.message);
    this.Db = j;
    this.Ga = m;
    this.b();
    return
  }
  '"OK"' != c && e(Error("__FC_connect failed? ret: " + c))
};
t.zb = function(a) {
  try {
    var b = this.za.CallFunction($d("__FC_writeFrames", this.W, a))
  }catch(c) {
    S(this.a, "writeFrames: could not call __FC_writeFrames; Flash probably crashed. Disposing now. Error was: " + c.message);
    this.Db = j;
    this.Ga = m;
    this.b();
    return
  }
  '"OK"' != b && ('"no such instance"' == b ? (T(this.a, "Flash no longer knows of " + this.W + "; disposing."), this.b()) : e(Error("__FC_writeFrames failed? ret: " + b)))
};
t.c = function() {
  this.a.info("in disposeInternal, needToCallClose_=" + this.Ga);
  te.g.c.call(this);
  var a = this.za;
  delete this.za;
  if(this.Ga) {
    try {
      var b = a.CallFunction($d("__FC_close", this.W));
      this.a.info("disposeInternal: __FC_close ret: " + b)
    }catch(c) {
      S(this.a, "disposeInternal: could not call __FC_close; Flash probably crashed. Error was: " + c.message), this.Db = j
    }
  }
  if(this.Db) {
    a = this.ta, T(a.a, "oncrash"), xe(a.A, j)
  }else {
    this.ta.onclose()
  }
  delete this.ta;
  delete this.ic.Qa[this.W]
};
function ye(a, b) {
  L.call(this);
  this.p = a;
  this.za = b;
  this.Qa = {};
  this.sc = "__FST_" + me();
  u[this.sc] = C(this.Ye, this);
  var c = b.CallFunction($d("__FC_setCallbackFunc", this.sc));
  '"OK"' != c && e(Error("__FC_setCallbackFunc failed? ret: " + c))
}
E(ye, L);
t = ye.prototype;
t.a = W("cw.net.FlashSocketTracker");
t.B = function(a, b) {
  a.push("<FlashSocketTracker instances=");
  O(this.Qa, a, b);
  a.push(">")
};
t.wc = function(a) {
  a = new te(this, a);
  return this.Qa[a.W] = a
};
t.We = function(a, b, c, d) {
  var g = this.Qa[a];
  g ? "frames" == b && d ? (ue(g, "ioerror", "FlashConnector hadError while handling data."), g.b()) : ue(g, b, c) : T(this.a, "Cannot dispatch because we have no instance: " + P([a, b, c, d]))
};
t.Ye = function(a, b, c, d) {
  try {
    var g = this.p;
    g.Fb.push([this.We, this, [a, b, c, d]]);
    g.hd == k && (g.hd = g.w.setTimeout(g.Qe, 0))
  }catch(f) {
    u.window.setTimeout(function() {
      e(f)
    }, 0)
  }
};
t.c = function() {
  ye.g.c.call(this);
  for(var a = $a(this.Qa);a.length;) {
    a.pop().b()
  }
  delete this.Qa;
  delete this.za;
  u[this.sc] = h
};
function ze(a) {
  L.call(this);
  this.A = a;
  this.eb = []
}
E(ze, L);
t = ze.prototype;
t.a = W("cw.net.FlashSocketConduit");
t.zb = function(a) {
  this.eb ? (V(this.a, "writeFrames: Not connected, can't write " + a.length + " frame(s) yet."), this.eb.push.apply(this.eb, a)) : (V(this.a, "writeFrames: Writing " + a.length + " frame(s)."), this.fc.zb(a))
};
t.tc = function(a, b) {
  this.fc.tc(a, b)
};
t.onconnect = function() {
  this.a.info("onconnect");
  ve(this.A);
  var a = this.eb;
  this.eb = k;
  a.length && (V(this.a, "onconnect: Writing " + a.length + " buffered frame(s)."), this.fc.zb(a))
};
t.onclose = function() {
  this.a.info("onclose");
  xe(this.A, m)
};
t.c = function() {
  this.a.info("in disposeInternal.");
  ze.g.c.call(this);
  this.fc.b();
  delete this.A
};
var Ae = [];
function Be() {
  var a = new Qb;
  Ae.push(a);
  return a
}
function Ce(a) {
  var b = Ae;
  Ae = [];
  hb(b, function(b) {
    Wb(b, a)
  });
  return k
}
function De(a) {
  var b = Ae;
  Ae = [];
  hb(b, function(b) {
    b.Ma(a)
  });
  return k
}
;var re = Math.pow(2, 53);
var Ee = {Le:q("<cw.eq.Wildcard>")};
function Fe(a) {
  return"boolean" == a || "number" == a || "null" == a || "undefined" == a || "string" == a
}
function Ge(a, b, c) {
  var d = fa(a), g = fa(b);
  if(a == Ee || b == Ee) {
    return j
  }
  if(a != k && "function" == typeof a.O) {
    return c && c.push("running custom equals function on left object"), a.O(b, c)
  }
  if(b != k && "function" == typeof b.O) {
    return c && c.push("running custom equals function on right object"), b.O(a, c)
  }
  if(Fe(d) || Fe(g)) {
    a = a === b
  }else {
    if(a instanceof RegExp && b instanceof RegExp) {
      a = a.toString() === b.toString()
    }else {
      if(ia(a) && ia(b)) {
        a = a.valueOf() === b.valueOf()
      }else {
        if("array" == d && "array" == g) {
          a: {
            if(c && c.push("descending into array"), a.length != b.length) {
              c && c.push("array length mismatch: " + a.length + ", " + b.length), a = m
            }else {
              d = 0;
              for(g = a.length;d < g;d++) {
                if(!Ge(a[d], b[d], c)) {
                  c && c.push("earlier comparisons indicate mismatch at array item #" + d);
                  a = m;
                  break a
                }
              }
              c && c.push("ascending from array");
              a = j
            }
          }
        }else {
          if(a.Ke == Ca && b.Ke == Ca) {
            a: {
              c && c.push("descending into object");
              for(var f in a) {
                if(!(f in b)) {
                  c && c.push("property " + f + " missing on right object");
                  a = m;
                  break a
                }
                if(!Ge(a[f], b[f], c)) {
                  c && c.push("earlier comparisons indicate mismatch at property " + f);
                  a = m;
                  break a
                }
              }
              for(f in b) {
                if(!(f in a)) {
                  c && c.push("property " + f + " missing on left object");
                  a = m;
                  break a
                }
              }
              c && c.push("ascending from object");
              a = j
            }
          }else {
            a = a === b
          }
        }
      }
    }
  }
  return a
}
;function X(a, b) {
  this.yf = a;
  this.Yb = b
}
X.prototype.O = function(a, b) {
  return ja(a) && this.constructor == a.constructor && Ge(this.Yb, a.Yb, b)
};
X.prototype.B = function(a, b) {
  a.push("new ", this.yf, "(");
  for(var c = "", d = 0;d < this.Yb.length;d++) {
    a.push(c), c = ", ", O(this.Yb[d], a, b)
  }
  a.push(")")
};
function Y(a) {
  F.call(this, a)
}
E(Y, F);
Y.prototype.name = "cw.net.InvalidFrame";
function He() {
  var a = [];
  this.S(a);
  return a.join("")
}
function Ie() {
}
Ie.prototype.O = function(a, b) {
  return!(a instanceof Ie) ? m : Ge(Je(this), Je(a), b)
};
Ie.prototype.B = function(a, b) {
  a.push("<HelloFrame properties=");
  O(Je(this), a, b);
  a.push(">")
};
function Je(a) {
  return[a.ea, a.oe, a.Qd, a.se, a.vb, a.ed, a.ge, a.ee, a.Mc, a.ce, a.He, a.De, a.wa, a.Sb]
}
Ie.prototype.N = He;
Ie.prototype.S = function(a) {
  var b = {};
  b.tnum = this.ea;
  b.ver = this.oe;
  b.format = this.Qd;
  b["new"] = this.se;
  b.id = this.vb;
  b.ming = this.ed;
  b.pad = this.ge;
  b.maxb = this.ee;
  w(this.Mc) && (b.maxt = this.Mc);
  b.maxia = this.ce;
  b.tcpack = this.He;
  b.eeds = this.De;
  b.sack = this.wa instanceof Sd ? ne((new Ke(this.wa)).N()) : this.wa;
  b.seenack = this.Sb instanceof Sd ? ne((new Ke(this.Sb)).N()) : this.Sb;
  for(var c in b) {
    b[c] === h && delete b[c]
  }
  a.push(dc(b), "H")
};
function Le(a) {
  X.call(this, "StringFrame", [a]);
  this.gd = a
}
E(Le, X);
Le.prototype.N = He;
Le.prototype.S = function(a) {
  a.push(this.gd, " ")
};
function Me(a) {
  X.call(this, "CommentFrame", [a]);
  this.Se = a
}
E(Me, X);
Me.prototype.N = He;
Me.prototype.S = function(a) {
  a.push(this.Se, "^")
};
function Ne(a) {
  X.call(this, "SeqNumFrame", [a]);
  this.xe = a
}
E(Ne, X);
Ne.prototype.N = He;
Ne.prototype.S = function(a) {
  a.push(String(this.xe), "N")
};
function Oe(a) {
  var b = a.split("|");
  if(2 != b.length) {
    return k
  }
  a: {
    var c = b[1], a = re;
    if(pe.test(c) && (c = parseInt(c, 10), -1 <= c && c <= a)) {
      a = c;
      break a
    }
    a = k
  }
  if(a == k) {
    return k
  }
  c = [];
  if(b[0]) {
    for(var b = b[0].split(","), d = 0, g = b.length;d < g;d++) {
      var f = qe(b[d]);
      if(f == k) {
        return k
      }
      c.push(f)
    }
  }
  return new Sd(a, c)
}
function Ke(a) {
  X.call(this, "SackFrame", [a]);
  this.wa = a
}
E(Ke, X);
Ke.prototype.N = He;
Ke.prototype.S = function(a) {
  var b = this.wa;
  a.push(b.Ja.join(","), "|", String(b.La));
  a.push("A")
};
function Pe(a) {
  X.call(this, "StreamStatusFrame", [a]);
  this.Zd = a
}
E(Pe, X);
Pe.prototype.N = He;
Pe.prototype.S = function(a) {
  var b = this.Zd;
  a.push(b.Ja.join(","), "|", String(b.La));
  a.push("T")
};
function Qe() {
  X.call(this, "StreamCreatedFrame", [])
}
E(Qe, X);
Qe.prototype.N = He;
Qe.prototype.S = function(a) {
  a.push("C")
};
function Re() {
  X.call(this, "YouCloseItFrame", [])
}
E(Re, X);
Re.prototype.N = He;
Re.prototype.S = function(a) {
  a.push("Y")
};
function Se(a, b) {
  X.call(this, "ResetFrame", [a, b]);
  this.qe = a;
  this.od = b
}
E(Se, X);
Se.prototype.N = He;
Se.prototype.S = function(a) {
  a.push(this.qe, "|", String(Number(this.od)), "!")
};
var Te = {stream_attach_failure:"stream_attach_failure", acked_unsent_strings:"acked_unsent_strings", invalid_frame_type_or_arguments:"invalid_frame_type_or_arguments", frame_corruption:"frame_corruption", rwin_overflow:"rwin_overflow"};
function Ue(a) {
  X.call(this, "TransportKillFrame", [a]);
  this.reason = a
}
E(Ue, X);
Ue.prototype.N = He;
Ue.prototype.S = function(a) {
  a.push(this.reason, "K")
};
function Ve(a) {
  a || e(new Y("0-length frame"));
  var b = a.substr(a.length - 1, 1);
  if(" " == b) {
    return new Le(a.substr(0, a.length - 1))
  }
  if("A" == b) {
    return a = Oe(ne(a)), a == k && e(new Y("bad sack")), new Ke(a)
  }
  if("N" == b) {
    return a = qe(ne(a)), a == k && e(new Y("bad seqNum")), new Ne(a)
  }
  if("T" == b) {
    return a = Oe(ne(a)), a == k && e(new Y("bad lastSackSeen")), new Pe(a)
  }
  if("Y" == b) {
    return 1 != a.length && e(new Y("leading garbage")), new Re
  }
  if("^" == b) {
    return new Me(a.substr(0, a.length - 1))
  }
  if("C" == b) {
    return 1 != a.length && e(new Y("leading garbage")), new Qe
  }
  if("!" == b) {
    return b = a.substr(0, a.length - 3), (255 < b.length || !/^([ -~]*)$/.test(b)) && e(new Y("bad reasonString")), a = {"|0":m, "|1":j}[a.substr(a.length - 3, 2)], a == k && e(new Y("bad applicationLevel")), new Se(b, a)
  }
  if("K" == b) {
    return a = a.substr(0, a.length - 1), a = Te[a], a == k && e(new Y("unknown kill reason: " + a)), new Ue(a)
  }
  e(new Y("Invalid frame type " + b))
}
;var We = RegExp("^(?:([^:/?#.]+):)?(?://(?:([^/?#]*)@)?([\\w\\d\\-\\u0100-\\uffff.%]*)(?::([0-9]+))?)?([^?#]+)?(?:\\?([^#]*))?(?:#(.*))?$");
function Xe(a, b) {
  var c = a.match(We), d = b.match(We);
  return c[3] == d[3] && c[1] == d[1] && c[4] == d[4]
}
;function Ye(a, b) {
  var c;
  a instanceof Ye ? (this.P = w(b) ? b : a.P, Ze(this, a.xa), $e(this, a.xb), af(this, a.ka), bf(this, a.Ya), cf(this, a.ra), df(this, a.I.L()), ef(this, a.ib)) : a && (c = String(a).match(We)) ? (this.P = !!b, Ze(this, c[1] || "", j), $e(this, c[2] || "", j), af(this, c[3] || "", j), bf(this, c[4]), cf(this, c[5] || "", j), df(this, c[6] || "", j), ef(this, c[7] || "", j)) : (this.P = !!b, this.I = new ff(k, 0, this.P))
}
t = Ye.prototype;
t.xa = "";
t.xb = "";
t.ka = "";
t.Ya = k;
t.ra = "";
t.ib = "";
t.lf = m;
t.P = m;
t.toString = function() {
  var a = [], b = this.xa;
  b && a.push(gf(b, hf), ":");
  if(b = this.ka) {
    a.push("//");
    var c = this.xb;
    c && a.push(gf(c, hf), "@");
    a.push(encodeURIComponent(String(b)));
    b = this.Ya;
    b != k && a.push(":", String(b))
  }
  if(b = this.ra) {
    this.ka && "/" != b.charAt(0) && a.push("/"), a.push(gf(b, "/" == b.charAt(0) ? jf : kf))
  }
  (b = this.I.toString()) && a.push("?", b);
  (b = this.ib) && a.push("#", gf(b, lf));
  return a.join("")
};
t.L = function() {
  return new Ye(this)
};
function Ze(a, b, c) {
  mf(a);
  a.xa = c ? b ? decodeURIComponent(b) : "" : b;
  a.xa && (a.xa = a.xa.replace(/:$/, ""))
}
function $e(a, b, c) {
  mf(a);
  a.xb = c ? b ? decodeURIComponent(b) : "" : b
}
function af(a, b, c) {
  mf(a);
  a.ka = c ? b ? decodeURIComponent(b) : "" : b
}
function bf(a, b) {
  mf(a);
  b ? (b = Number(b), (isNaN(b) || 0 > b) && e(Error("Bad port number " + b)), a.Ya = b) : a.Ya = k
}
function cf(a, b, c) {
  mf(a);
  a.ra = c ? b ? decodeURIComponent(b) : "" : b
}
function df(a, b, c) {
  mf(a);
  b instanceof ff ? (a.I = b, a.I.Yc(a.P)) : (c || (b = gf(b, nf)), a.I = new ff(b, 0, a.P))
}
function ef(a, b, c) {
  mf(a);
  a.ib = c ? b ? decodeURIComponent(b) : "" : b
}
function mf(a) {
  a.lf && e(Error("Tried to modify a read-only Uri"))
}
t.Yc = function(a) {
  this.P = a;
  this.I && this.I.Yc(a);
  return this
};
function of(a) {
  return a instanceof Ye ? a.L() : new Ye(a, h)
}
function gf(a, b) {
  return x(a) ? encodeURI(a).replace(b, pf) : k
}
function pf(a) {
  a = a.charCodeAt(0);
  return"%" + (a >> 4 & 15).toString(16) + (a & 15).toString(16)
}
var hf = /[#\/\?@]/g, kf = /[\#\?:]/g, jf = /[\#\?]/g, nf = /[\#\?@]/g, lf = /#/g;
function ff(a, b, c) {
  this.D = a || k;
  this.P = !!c
}
function qf(a) {
  if(!a.n && (a.n = new ld, a.d = 0, a.D)) {
    for(var b = a.D.split("&"), c = 0;c < b.length;c++) {
      var d = b[c].indexOf("="), g = k, f = k;
      0 <= d ? (g = b[c].substring(0, d), f = b[c].substring(d + 1)) : g = b[c];
      g = decodeURIComponent(g.replace(/\+/g, " "));
      g = rf(a, g);
      a.add(g, f ? decodeURIComponent(f.replace(/\+/g, " ")) : "")
    }
  }
}
t = ff.prototype;
t.n = k;
t.d = k;
t.F = function() {
  qf(this);
  return this.d
};
t.add = function(a, b) {
  qf(this);
  this.D = k;
  var a = rf(this, a), c = this.n.get(a);
  c || this.n.set(a, c = []);
  c.push(b);
  this.d++;
  return this
};
t.remove = function(a) {
  qf(this);
  a = rf(this, a);
  return this.n.ja(a) ? (this.D = k, this.d -= this.n.get(a).length, this.n.remove(a)) : m
};
t.clear = function() {
  this.n = this.D = k;
  this.d = 0
};
t.Ra = function() {
  qf(this);
  return 0 == this.d
};
t.ja = function(a) {
  qf(this);
  a = rf(this, a);
  return this.n.ja(a)
};
t.uc = function(a) {
  var b = this.C();
  return mb(b, a)
};
t.ba = function() {
  qf(this);
  for(var a = this.n.C(), b = this.n.ba(), c = [], d = 0;d < b.length;d++) {
    for(var g = a[d], f = 0;f < g.length;f++) {
      c.push(b[d])
    }
  }
  return c
};
t.C = function(a) {
  qf(this);
  var b = [];
  if(a) {
    this.ja(a) && (b = ob(b, this.n.get(rf(this, a))))
  }else {
    for(var a = this.n.C(), c = 0;c < a.length;c++) {
      b = ob(b, a[c])
    }
  }
  return b
};
t.set = function(a, b) {
  qf(this);
  this.D = k;
  a = rf(this, a);
  this.ja(a) && (this.d -= this.n.get(a).length);
  this.n.set(a, [b]);
  this.d++;
  return this
};
t.get = function(a, b) {
  var c = a ? this.C(a) : [];
  return 0 < c.length ? String(c[0]) : b
};
t.toString = function() {
  if(this.D) {
    return this.D
  }
  if(!this.n) {
    return""
  }
  for(var a = [], b = this.n.ba(), c = 0;c < b.length;c++) {
    for(var d = b[c], g = encodeURIComponent(String(d)), d = this.C(d), f = 0;f < d.length;f++) {
      var i = g;
      "" !== d[f] && (i += "=" + encodeURIComponent(String(d[f])));
      a.push(i)
    }
  }
  return this.D = a.join("&")
};
t.L = function() {
  var a = new ff;
  a.D = this.D;
  this.n && (a.n = this.n.L(), a.d = this.d);
  return a
};
function rf(a, b) {
  var c = String(b);
  a.P && (c = c.toLowerCase());
  return c
}
t.Yc = function(a) {
  a && !this.P && (qf(this), this.D = k, jd(this.n, function(a, c) {
    var d = c.toLowerCase();
    c != d && (this.remove(c), this.remove(d), 0 < a.length && (this.D = k, this.n.set(rf(this, d), pb(a)), this.d += a.length))
  }, this));
  this.P = a
};
function sf(a, b, c, d) {
  this.contentWindow = a;
  this.Gb = b;
  this.fd = c;
  this.cf = d
}
sf.prototype.B = function(a, b) {
  a.push("<XDRFrame frameId=");
  O(this.cf, a, b);
  a.push(", expandedUrl=");
  O(this.Gb, a, b);
  a.push(", streams=");
  O(this.fd, a, b);
  a.push(">")
};
function tf() {
  this.frames = [];
  this.Kc = new ld
}
tf.prototype.a = W("cw.net.XDRTracker");
function uf(a, b) {
  for(var c = vf, d = 0;d < c.frames.length;d++) {
    var g = c.frames[d], f;
    if(f = 0 == g.fd.length) {
      f = g.Gb;
      var i = String(a).replace(/([-()\[\]{}+?*.$\^|,:#<!\\])/g, "\\$1").replace(/\x08/g, "\\x08").replace(/%random%/g, "ml" + Array(21).join("\\d"));
      f = RegExp("^" + i + "$").test(f)
    }
    if(f) {
      return c.a.info("Giving " + P(b) + " existing frame " + P(g)), Zb(g)
    }
  }
  d = me() + me();
  g = a.replace(/%random%/g, function() {
    return"ml" + String(Math.floor(kc())) + String(Math.floor(kc()))
  });
  f = u.location;
  f instanceof Ye || (f = of(f));
  g instanceof Ye || (g = of(g));
  var l = f;
  f = l.L();
  (i = !!g.xa) ? Ze(f, g.xa) : i = !!g.xb;
  i ? $e(f, g.xb) : i = !!g.ka;
  i ? af(f, g.ka) : i = g.Ya != k;
  var n = g.ra;
  if(i) {
    bf(f, g.Ya)
  }else {
    if(i = !!g.ra) {
      if("/" != n.charAt(0) && (l.ka && !l.ra ? n = "/" + n : (l = f.ra.lastIndexOf("/"), -1 != l && (n = f.ra.substr(0, l + 1) + n))), ".." == n || "." == n) {
        n = ""
      }else {
        if(-1 != n.indexOf("./") || -1 != n.indexOf("/.")) {
          for(var l = 0 == n.lastIndexOf("/", 0), n = n.split("/"), s = [], A = 0;A < n.length;) {
            var r = n[A++];
            "." == r ? l && A == n.length && s.push("") : ".." == r ? ((1 < s.length || 1 == s.length && "" != s[0]) && s.pop(), l && A == n.length && s.push("")) : (s.push(r), l = j)
          }
          n = s.join("/")
        }
      }
    }
  }
  i ? cf(f, n) : i = "" !== g.I.toString();
  i ? df(f, g.I.toString() ? decodeURIComponent(g.I.toString()) : "") : i = !!g.ib;
  i && ef(f, g.ib);
  g = f.toString();
  f = String(u.location).match(We)[3] || k;
  i = g.match(We)[3] || k;
  f == i ? (c.a.info("No need to make a real XDRFrame for " + P(b)), c = Zb(new sf(u, g, [b], k))) : ((f = Q("minerva-elements")) || e(Error('makeWindowForUrl_: Page is missing an empty div with id "minerva-elements"; please add one.')), i = new Qb, c.Kc.set(d, [i, g, b]), c.a.info("Creating new XDRFrame " + P(d) + "for " + P(b)), c = zc("iframe", {id:"minerva-xdrframe-" + d, style:"visibility: hidden; height: 0; width: 0; border: 0; margin: 0;", src:g + "xdrframe/?domain=" + document.domain + "&id=" + 
  d}), f.appendChild(c), c = i);
  return c
}
tf.prototype.Sf = function(a) {
  var b = this.Kc.get(a);
  b || e(Error("Unknown frameId " + P(a)));
  this.Kc.remove(b);
  var c = b[0], a = new sf(Q("minerva-xdrframe-" + a).contentWindow || (Q("minerva-xdrframe-" + a).contentDocument || Q("minerva-xdrframe-" + a).contentWindow.document).parentWindow || (Q("minerva-xdrframe-" + a).contentDocument || Q("minerva-xdrframe-" + a).contentWindow.document).defaultView, b[1], [b[2]], a);
  this.frames.push(a);
  Wb(c, a)
};
var vf = new tf;
u.__XHRTracker_xdrFrameLoaded = C(vf.Sf, vf);
var wf;
wf = m;
var xf = Ha();
xf && (-1 != xf.indexOf("Firefox") || -1 != xf.indexOf("Camino") || -1 != xf.indexOf("iPhone") || -1 != xf.indexOf("iPod") || -1 != xf.indexOf("iPad") || -1 != xf.indexOf("Android") || -1 != xf.indexOf("Chrome") && (wf = j));
var yf = wf;
function zf(a, b, c, d, g, f) {
  Qb.call(this, g, f);
  this.be = a;
  this.xc = [];
  this.Cd = !!b;
  this.af = !!c;
  this.Te = !!d;
  for(b = 0;b < a.length;b++) {
    Xb(a[b], C(this.Id, this, b, j), C(this.Id, this, b, m))
  }
  0 == a.length && !this.Cd && Wb(this, this.xc)
}
E(zf, Qb);
zf.prototype.ie = 0;
zf.prototype.Id = function(a, b, c) {
  this.ie++;
  this.xc[a] = [b, c];
  this.na || (this.Cd && b ? Wb(this, [a, c]) : this.af && !b ? this.Ma(c) : this.ie == this.be.length && Wb(this, this.xc));
  this.Te && !b && (c = k);
  return c
};
zf.prototype.Ma = function(a) {
  zf.g.Ma.call(this, a);
  hb(this.be, function(a) {
    a.cancel()
  })
};
function Af(a, b) {
  this.Rf = a;
  this.de = b
}
Af.prototype.Jc = 0;
Af.prototype.Vb = 0;
Af.prototype.Cc = m;
function Bf(a) {
  var b = [];
  if(a.Cc) {
    return[b, 2]
  }
  var c = a.Jc, d = a.Rf.responseText;
  for(a.Jc = d.length;;) {
    c = d.indexOf("\n", c);
    if(-1 == c) {
      break
    }
    var g = d.substr(a.Vb, c - a.Vb), g = g.replace(/\r$/, "");
    if(g.length > a.de) {
      return a.Cc = j, [b, 2]
    }
    b.push(g);
    a.Vb = c += 1
  }
  return a.Jc - a.Vb - 1 > a.de ? (a.Cc = j, [b, 2]) : [b, 1]
}
;function Cf(a, b, c) {
  L.call(this);
  this.A = b;
  this.U = a;
  this.vc = c
}
E(Cf, L);
t = Cf.prototype;
t.a = W("cw.net.XHRMaster");
t.ua = -1;
t.Lc = function(a, b, c) {
  this.vc.__XHRSlave_makeRequest(this.U, a, b, c)
};
t.pa = p("ua");
t.Oc = function(a, b) {
  1 != b && S(this.a, P(this.U) + " got status != OK: " + b + "; XHRSlave should dispose soon.");
  ve(this.A);
  we(this.A, a)
};
t.Pc = function(a) {
  U(this.a, "ongotheaders_: " + P(a));
  var b = k;
  "Content-Length" in a && (b = qe(a["Content-Length"]));
  a = this.A;
  U(a.a, a.m() + " got Content-Length: " + b);
  a.Z == Df && (b == k && (T(a.a, "Expected to receive a valid Content-Length, but did not."), b = 5E5), Ef(a, 2E3 + 1E3 * (b / 3072)))
};
t.Qc = function(a) {
  1 != a && U(this.a, this.A.m() + "'s XHR's readyState is " + a);
  this.ua = a;
  2 <= this.ua && ve(this.A)
};
t.Nc = function() {
  this.A.b()
};
t.c = function() {
  Cf.g.c.call(this);
  delete Ff.ca[this.U];
  this.vc.__XHRSlave_dispose(this.U);
  delete this.vc
};
function Gf() {
  L.call(this);
  this.ca = {}
}
E(Gf, L);
t = Gf.prototype;
t.a = W("cw.net.XHRMasterTracker");
t.wc = function(a, b) {
  var c = "_" + me(), d = new Cf(c, a, b);
  return this.ca[c] = d
};
t.Oc = function(a, b, c) {
  if(H) {
    for(var d = [], g = 0, f = b.length;g < f;g++) {
      d[g] = b[g]
    }
    b = d
  }else {
    b = ob(b)
  }
  (d = this.ca[a]) ? d.Oc(b, c) : S(this.a, "onframes_: no master for " + P(a))
};
t.Pc = function(a, b) {
  var c = this.ca[a];
  c ? c.Pc(b) : S(this.a, "ongotheaders_: no master for " + P(a))
};
t.Qc = function(a, b) {
  var c = this.ca[a];
  c ? c.Qc(b) : S(this.a, "onreadystatechange_: no master for " + P(a))
};
t.Nc = function(a) {
  var b = this.ca[a];
  b ? (delete this.ca[b.U], b.Nc()) : S(this.a, "oncomplete_: no master for " + P(a))
};
t.c = function() {
  Gf.g.c.call(this);
  for(var a = $a(this.ca);a.length;) {
    a.pop().b()
  }
  delete this.ca
};
var Ff = new Gf;
u.__XHRMaster_onframes = C(Ff.Oc, Ff);
u.__XHRMaster_oncomplete = C(Ff.Nc, Ff);
u.__XHRMaster_ongotheaders = C(Ff.Pc, Ff);
u.__XHRMaster_onreadystatechange = C(Ff.Qc, Ff);
function Hf(a, b, c) {
  this.X = a;
  this.host = b;
  this.port = c
}
function Kf(a, b, c) {
  this.host = a;
  this.port = b;
  this.Jf = c
}
function Lf(a, b) {
  b || (b = a);
  this.X = a;
  this.ya = b
}
Lf.prototype.B = function(a, b) {
  a.push("<HttpEndpoint primaryUrl=");
  O(this.X, a, b);
  a.push(", secondaryUrl=");
  O(this.ya, a, b);
  a.push(">")
};
function Mf(a, b, c, d) {
  this.X = a;
  this.ne = b;
  this.ya = c;
  this.we = d;
  (!(0 == this.X.indexOf("http://") || 0 == this.X.indexOf("https://")) || !(0 == this.ya.indexOf("http://") || 0 == this.ya.indexOf("https://"))) && e(Error("primaryUrl and secondUrl must be absolute URLs with http or https scheme"));
  a = this.ne.location.href;
  Xe(this.X, a) || e(Error("primaryWindow not same origin as primaryUrl: " + a));
  a = this.we.location.href;
  Xe(this.ya, a) || e(Error("secondaryWindow not same origin as secondaryUrl: " + a))
}
Mf.prototype.B = function(a, b) {
  a.push("<ExpandedHttpEndpoint_ primaryUrl=");
  O(this.X, a, b);
  a.push(", secondaryUrl=");
  O(this.ya, a, b);
  a.push(">")
};
var Nf = new Me(";)]}");
function Of() {
}
Of.prototype.Fd = q(1);
function Pf(a) {
  u.setTimeout(function() {
    w(a.message) && a.stack && (a.message += "\n" + a.stack);
    e(a)
  }, 0)
}
function Qf(a) {
  this.Ff = a
}
Qf.prototype.B = function(a, b) {
  a.push("<UserContext for ");
  O(this.Ff, a, b);
  a.push(">")
};
Qf.prototype.toString = function() {
  return P(this)
};
function Rf(a, b, c, d) {
  X.call(this, "TransportInfo", [a, b, c, d]);
  this.ea = a;
  this.Yg = b;
  this.ah = c;
  this.bh = d
}
E(Rf, X);
function Sf(a, b, c) {
  L.call(this);
  this.r = a;
  this.Gf = b ? b : new Of;
  this.p = c ? c : bc;
  this.wb = new qd;
  this.vb = me() + me();
  this.Y = new Td;
  this.Hc = new Vd;
  this.yb = k;
  this.jc = [];
  this.ab = new Qf(this);
  this.Pe = C(this.Mf, this);
  I && (this.yb = Gb(u, "load", this.zf, m, this))
}
E(Sf, L);
t = Sf.prototype;
t.a = W("cw.net.ClientStream");
t.$d = new Sd(-1, []);
t.ae = new Sd(-1, []);
t.pf = 50;
t.of = 1048576;
t.Sc = k;
t.Rc = k;
t.Tc = k;
t.Uc = k;
t.onreset = k;
t.le = k;
t.Za = k;
t.cd = m;
t.Xc = m;
t.e = "1_UNSTARTED";
t.jd = -1;
t.h = k;
t.q = k;
t.rb = k;
t.dd = 0;
t.me = 0;
t.ve = 0;
t.B = function(a, b) {
  a.push("<ClientStream id=");
  O(this.vb, a, b);
  a.push(", state=", String(this.e));
  a.push(", primary=");
  O(this.h, a, b);
  a.push(", secondary=");
  O(this.q, a, b);
  a.push(", resetting=");
  O(this.rb, a, b);
  a.push(">")
};
t.toString = function() {
  return P(this)
};
function Tf(a) {
  var b = [-1];
  a.h && b.push(a.h.Xa);
  a.q && b.push(a.q.Xa);
  return Math.max.apply(Math.max, b)
}
function Uf(a) {
  if(!("3_STARTED" > a.e)) {
    Vf(a);
    var b = 0 != a.Y.G.F(), c = Xd(a.Hc), d = !c.O(a.ae) && !(a.h && c.O(a.h.Ua) || a.q && c.O(a.q.Ua)), g = Tf(a);
    if((b = b && g < a.Y.Ca) || d) {
      var f = b && d ? "string(s)+SACK" : b ? "string(s)" : d ? "SACK" : "nothing!?";
      a.h.Ba ? (V(a.a, "tryToSend_: writing " + f + " to primary"), d && (d = a.h, c != d.Ua && (!d.da && !d.s.length && Wf(d), d.s.push(new Ke(c)), d.Ua = c)), b && Xf(a.h, a.Y, g + 1), a.h.aa()) : a.q == k ? a.cd ? (V(a.a, "tryToSend_: creating secondary to send " + f), a.q = Yf(a, m, j), a.q && (b && Xf(a.q, a.Y, g + 1), a.q.aa())) : (V(a.a, "tryToSend_: not creating a secondary because stream might not exist on server"), a.Xc = j) : V(a.a, "tryToSend_: need to send " + f + ", but can't right now")
    }
  }
}
function Vf(a) {
  a.Za != k && (a.p.w.clearTimeout(a.Za), a.Za = k)
}
t.Mf = function() {
  this.Za = k;
  Uf(this)
};
function Zf(a) {
  a.Za == k && (a.Za = a.p.w.setTimeout(a.Pe, 6))
}
t.zf = function() {
  this.yb = k;
  if(this.h && this.h.Sa()) {
    this.a.info("restartHttpRequests_: aborting primary");
    var a = this.h;
    a.lc = j;
    a.b()
  }
  this.q && this.q.Sa() && (this.a.info("restartHttpRequests_: aborting secondary"), a = this.q, a.lc = j, a.b())
};
function $f(a, b) {
  var c;
  w(c) || (c = j);
  "3_STARTED" < a.e && e(Error("sendString: Can't send in state " + a.e));
  c && (x(b) || e(Error("sendString: not a string: " + P(b))), /^([ -~]*)$/.test(b) || e(Error("sendString: string has illegal chars: " + P(b))));
  a.Y.append(b);
  Zf(a)
}
function Yf(a, b, c) {
  var d;
  a.r instanceof Mf ? d = 1 == a.Gf.Fd() ? Df : ag : a.r instanceof Kf ? d = bg : e(Error("Don't support endpoint " + P(a.r)));
  a.jd += 1;
  b = new cg(a.p, a, a.jd, d, a.r, b);
  V(a.a, "Created: " + b.m());
  if(c) {
    if(a.Tc) {
      c = new Rf(b.ea, b.ha, b.va, b.Ba);
      try {
        a.Tc.call(a.ab, c)
      }catch(g) {
        T(a.a, "ontransportcreated raised uncaught exception", g), Pf(g)
      }
    }
    if(dg(a)) {
      return k
    }
  }
  a.wb.add(b);
  return b
}
function eg(a, b, c) {
  var d = new fg(a.p, a, b, c);
  V(a.a, "Created: " + d.m() + ", delay=" + b + ", times=" + c);
  a.wb.add(d);
  return d
}
function gg(a, b) {
  a.wb.remove(b) || e(Error("transportOffline_: Transport was not removed?"));
  U(a.a, "Offline: " + b.m());
  var c = "4_RESETTING" == a.e && b.Je;
  if(b instanceof cg && !c) {
    if(a.Uc) {
      var d = new Rf(b.ea, b.ha, b.va, b.Ba);
      try {
        a.Uc.call(a.ab, d)
      }catch(g) {
        T(a.a, "ontransportdestroyed raised uncaught exception", g), Pf(g)
      }
    }
    if(dg(a)) {
      return
    }
  }
  a.dd = b.sa ? a.dd + b.sa : 0;
  1 <= a.dd && (a.a.info("transportOffline_: Doing an internal reset because streamPenalty_ reached limit."), hg(a, "stream penalty reached limit", m), a.b());
  if("3_STARTED" < a.e) {
    c ? (U(a.a, "Disposing because resettingTransport_ is done."), a.b()) : U(a.a, "Not creating a transport because ClientStream is in state " + a.e)
  }else {
    c = b instanceof fg;
    if(!c && b.lc) {
      var f = I ? yf ? [0, 1] : [9, 20] : [0, 0], c = f[0], d = f[1];
      V(a.a, "getDelayForNextTransport_: " + P({delay:c, times:d}))
    }else {
      if(d = b.sd(), b == a.h ? d ? f = ++a.me : c || (f = a.me = 0) : d ? f = ++a.ve : c || (f = a.ve = 0), c || !f) {
        d = c = 0, V(a.a, "getDelayForNextTransport_: " + P({count:f, delay:c, times:d}))
      }else {
        var i = 2E3 * Math.min(f, 3), l = Math.floor(4E3 * Math.random()) - 2E3, n = Math.max(0, b.Ge - b.kd), d = (c = Math.max(0, i + l - n)) ? 1 : 0;
        V(a.a, "getDelayForNextTransport_: " + P({count:f, base:i, variance:l, oldDuration:n, delay:c, times:d}))
      }
    }
    c = [c, d];
    f = c[0];
    c = c[1];
    if(b == a.h) {
      a.h = k;
      if(c) {
        a.h = eg(a, f, c)
      }else {
        f = Tf(a);
        a.h = Yf(a, j, j);
        if(!a.h) {
          return
        }
        Xf(a.h, a.Y, f + 1)
      }
      a.h.aa()
    }else {
      b == a.q && (a.q = k, c ? (a.q = eg(a, f, c), a.q.aa()) : Uf(a))
    }
  }
}
function hg(a, b, c) {
  if(a.onreset) {
    try {
      a.onreset.call(a.ab, b, c)
    }catch(d) {
      T(a.a, "onreset raised uncaught exception", d), Pf(d)
    }
  }
}
t.reset = function(a) {
  "3_STARTED" < this.e && e(Error("reset: Can't send reset in state " + this.e));
  Vf(this);
  0 != this.Y.G.F() && T(this.a, "reset: strings in send queue will never be sent: " + P(this.Y));
  this.e = "4_RESETTING";
  this.h && this.h.Ba ? (this.a.info("reset: Sending ResetFrame over existing primary."), ig(this.h, a), this.h.aa()) : (this.h && (U(this.a, "reset: Disposing primary before sending ResetFrame."), this.h.b()), this.q && (U(this.a, "reset: Disposing secondary before sending ResetFrame."), this.q.b()), this.a.info("reset: Creating resettingTransport_ for sending ResetFrame."), this.rb = Yf(this, m, m), ig(this.rb, a), this.rb.aa());
  hg(this, a, j)
};
function dg(a) {
  return"4_RESETTING" == a.e || a.$
}
t.zd = function(a) {
  S(this.a, "Failed to start " + P(this) + "; error was " + P(a.message));
  this.b();
  return k
};
t.start = function() {
  this.onmessage && e(Error("ClientStream.start: Hey, you! It's `onstring`, not `onmessage`! Refusing to start."));
  "1_UNSTARTED" != this.e && e(Error("ClientStream.start: " + P(this) + " already started"));
  this.Rc && this.Rc(this);
  this.e = "2_WAITING_RESOURCES";
  if(this.r instanceof Lf) {
    var a = uf(this.r.X, this), b = uf(this.r.ya, this), a = new zf([a, b], m, j);
    Xb(a, function(a) {
      return jb(a, function(a) {
        return a[1]
      })
    }, k, h);
    b = C(this.$e, this);
    Xb(a, b, k, h);
    b = C(this.zd, this);
    Xb(a, k, b, h)
  }else {
    if(this.r instanceof Hf) {
      if(Rd) {
        this.Bd()
      }else {
        a = this.p;
        b = this.r.X;
        if(Ae.length) {
          a = Be()
        }else {
          b = new ke(b + "FlashConnector.swf?cb=4bdfc178fc0e508c0cd5efc3fdb09920");
          b.pd = "#777777";
          le(b, 300, 30);
          var c = Q("minerva-elements");
          c || e(Error('loadFlashConnector_: Page is missing an empty div with id "minerva-elements"; please add one.'));
          var d = Q("minerva-elements-FlashConnectorSwf");
          d || (d = zc("div", {id:"minerva-elements-FlashConnectorSwf"}), c.appendChild(d));
          var g = a.w, f;
          var a = d, i, l = function() {
            i && delete u.__loadFlashObject_callbacks[i]
          };
          if(H && !J("1.8.1.20")) {
            f = $b(new se("Flash corrupts Error hierarchy in Firefox 2.0.0.0; disabled for all < 2.0.0.20"))
          }else {
            if(0 <= za(je, "9")) {
              var n;
              i = "_" + me();
              var s = new Qb(l);
              u.__loadFlashObject_callbacks[i] = function() {
                g.setTimeout(function() {
                  l();
                  Wb(s, Q(n))
                }, 0)
              };
              b.Hb.set("onloadcallback", '__loadFlashObject_callbacks["' + i + '"]()');
              n = Xc(b);
              Zc(b, a);
              f = s
            }else {
              f = $b(new se("Need Flash Player 9+; had " + (je ? je : "none")))
            }
          }
          var A = g.setTimeout(function() {
            f.cancel()
          }, 8E3), a = function(a) {
            g.clearTimeout(A);
            return a
          };
          Xb(f, a, a, h);
          Qd = f;
          a = Be();
          Xb(Qd, Ce, De)
        }
        var r = this;
        Xb(a, function(a) {
          Rd || (Rd = new ye(r.p, a));
          return k
        }, k, h);
        b = C(this.Bd, this);
        Xb(a, b, k, h);
        b = C(this.zd, this);
        Xb(a, k, b, h)
      }
    }else {
      jg(this)
    }
  }
};
t.$e = function(a) {
  var b = a[0].contentWindow, c = a[1].contentWindow, d = a[0].Gb, g = a[1].Gb;
  this.jc.push(a[0]);
  this.jc.push(a[1]);
  this.r = new Mf(d, b, g, c);
  jg(this)
};
t.Bd = function() {
  this.r = new Kf(this.r.host, this.r.port, Rd);
  jg(this)
};
function jg(a) {
  a.e = "3_STARTED";
  a.h = Yf(a, j, j);
  a.h && (Xf(a.h, a.Y, k), a.h.aa())
}
t.c = function() {
  this.a.info(P(this) + " in disposeInternal.");
  Vf(this);
  this.e = "5_DISCONNECTED";
  for(var a = this.wb.C(), b = 0;b < a.length;b++) {
    a[b].b()
  }
  for(a = 0;a < this.jc.length;a++) {
    nb(this.jc[a].fd, this)
  }
  I && this.yb && (Jb(this.yb), this.yb = k);
  this.le && this.le.call(this.ab);
  delete this.wb;
  delete this.h;
  delete this.q;
  delete this.rb;
  delete this.ab;
  Sf.g.c.call(this)
};
var Df = 1, ag = 2, bg = 3;
function cg(a, b, c, d, g, f) {
  L.call(this);
  this.p = a;
  this.v = b;
  this.ea = c;
  this.Z = d;
  this.r = g;
  this.s = [];
  this.ha = f;
  this.Ba = !this.Sa();
  this.va = this.Z != Df;
  this.Oe = C(this.Hf, this)
}
E(cg, L);
t = cg.prototype;
t.a = W("cw.net.ClientTransport");
t.l = k;
t.kd = k;
t.Ge = k;
t.Zb = k;
t.da = m;
t.gc = m;
t.Ua = k;
t.Ib = 0;
t.Xa = -1;
t.Xb = -1;
t.Je = m;
t.lc = m;
t.sa = 0;
t.kb = m;
t.B = function(a) {
  a.push("<ClientTransport #", String(this.ea), ", becomePrimary=", String(this.ha), ">")
};
t.m = function() {
  return(this.ha ? "Prim. T#" : "Sec. T#") + this.ea
};
t.sd = function() {
  return!(!this.kb && this.Ib)
};
t.Sa = function() {
  return this.Z == Df || this.Z == ag
};
function kg(a, b) {
  K.sort.call(b, function(a, b) {
    return a[0] > b[0] ? 1 : a[0] < b[0] ? -1 : 0
  } || rb);
  a: {
    var c = a.v, d = !a.va, g, f = c.Hc;
    g = c.pf;
    for(var i = c.of, l = [], n = m, s = 0, A = b.length;s < A;s++) {
      var r = b[s], y = r[0], r = r[1];
      if(y == f.Fa + 1) {
        f.Fa += 1;
        for(l.push(r);;) {
          y = f.Fa + 1;
          r = f.Aa.get(y, Yd);
          if(r === Yd) {
            break
          }
          l.push(r[0]);
          f.Aa.remove(y);
          f.J -= r[1];
          f.Fa = y
        }
      }else {
        if(!(y <= f.Fa)) {
          if(g != k && f.Aa.F() >= g) {
            n = j;
            break
          }
          var D = Pd(r);
          if(i != k && f.J + D > i) {
            n = j;
            break
          }
          f.Aa.set(y, [r, D]);
          f.J += D
        }
      }
    }
    f.Aa.Ra() && f.Aa.clear();
    g = [l, n];
    f = g[0];
    g = g[1];
    if(f) {
      for(i = 0;i < f.length;i++) {
        l = f[i];
        if(c.Sc) {
          try {
            c.Sc.call(c.ab, l)
          }catch(Fc) {
            T(c.a, "onstring raised uncaught exception", Fc), Pf(Fc)
          }
        }
        if(dg(c)) {
          break a
        }
      }
    }
    d || Zf(c);
    !dg(c) && g && (S(a.a, a.m() + "'s peer caused rwin overflow."), a.b())
  }
}
function lg(a, b, c) {
  try {
    var d = Ve(b);
    a.Ib += 1;
    U(a.a, a.m() + " RECV " + P(d));
    var g;
    1 == a.Ib && !d.O(Nf) && a.Sa() ? (T(a.a, a.m() + " is closing soon because got bad preamble: " + P(d)), g = j) : g = m;
    if(g) {
      return j
    }
    if(d instanceof Le) {
      if(!/^([ -~]*)$/.test(d.gd)) {
        return a.kb = j
      }
      a.Xb += 1;
      c.push([a.Xb, d.gd])
    }else {
      if(d instanceof Ke) {
        var f = a.v, i = d.wa;
        f.$d = i;
        var l = f.Y, n = i.La, c = m;
        n > l.Ca && (c = j);
        for(var s = Ud(l).concat(), d = 0;d < s.length;d++) {
          var A = s[d];
          if(A > n) {
            break
          }
          var r = l.G.get(A)[1];
          l.G.remove(A);
          l.J -= r
        }
        for(d = 0;d < i.Ja.length;d++) {
          var y = i.Ja[d];
          y > l.Ca && (c = j);
          l.G.ja(y) && (r = l.G.get(y)[1], l.G.remove(y), l.J -= r)
        }
        l.G.Ra() && l.G.clear();
        if(c) {
          return T(a.a, a.m() + " is closing soon because got bad SackFrame"), a.kb = j
        }
      }else {
        if(d instanceof Ne) {
          a.Xb = d.xe - 1
        }else {
          if(d instanceof Pe) {
            a.v.ae = d.Zd
          }else {
            if(d instanceof Re) {
              return V(a.a, a.m() + " is closing soon because got YouCloseItFrame"), j
            }
            if(d instanceof Ue) {
              return a.kb = j, "stream_attach_failure" == d.reason ? a.sa += 1 : "acked_unsent_strings" == d.reason && (a.sa += 0.5), V(a.a, a.m() + " is closing soon because got " + P(d)), j
            }
            if(!(d instanceof Me)) {
              if(d instanceof Qe) {
                var D = a.v, Fc = !a.va;
                V(D.a, "Stream is now confirmed to exist at server.");
                D.cd = j;
                D.Xc && !Fc && (D.Xc = m, Uf(D))
              }else {
                if(c.length) {
                  kg(a, c);
                  if(!ga(c)) {
                    for(var Wd = c.length - 1;0 <= Wd;Wd--) {
                      delete c[Wd]
                    }
                  }
                  c.length = 0
                }
                if(d instanceof Se) {
                  var If = a.v;
                  hg(If, d.qe, d.od);
                  If.b();
                  return j
                }
                e(Error(a.m() + " had unexpected state in framesReceived_."))
              }
            }
          }
        }
      }
    }
  }catch(Jf) {
    return Jf instanceof Y || e(Jf), T(a.a, a.m() + " is closing soon because got InvalidFrame: " + P(b)), a.kb = j
  }
  return m
}
function we(a, b) {
  a.gc = j;
  try {
    for(var c = m, d = [], g = 0, f = b.length;g < f;g++) {
      if(a.$) {
        a.a.info(a.m() + " returning from loop because we're disposed.");
        return
      }
      if(c = lg(a, b[g], d)) {
        break
      }
    }
    d.length && kg(a, d);
    a.gc = m;
    a.s.length && a.aa();
    c && (V(a.a, a.m() + " closeSoon is true.  Frames were: " + P(b)), a.b())
  }finally {
    a.gc = m
  }
}
t.Hf = function() {
  T(this.a, this.m() + " timed out due to lack of connection or no data being received.");
  this.b()
};
function mg(a) {
  a.Zb != k && (a.p.w.clearTimeout(a.Zb), a.Zb = k)
}
function Ef(a, b) {
  mg(a);
  b = Math.round(b);
  a.Zb = a.p.w.setTimeout(a.Oe, b);
  U(a.a, a.m() + "'s receive timeout set to " + b + " ms.")
}
function ve(a) {
  a.Z != Df && (a.Z == bg || a.Z == ag ? Ef(a, 13500) : e(Error("peerStillAlive_: Don't know what to do for this transportType: " + a.Z)))
}
function Wf(a) {
  var b = new Ie;
  b.ea = a.ea;
  b.oe = 2;
  b.Qd = 2;
  a.v.cd || (b.se = j);
  b.vb = a.v.vb;
  b.ed = a.va;
  b.ed && (b.ge = 4096);
  b.ee = 3E5;
  b.ce = a.va ? Math.floor(10) : 0;
  b.He = m;
  a.ha && (b.De = k, b.Mc = Math.floor((a.va ? 358E4 : 25E3) / 1E3));
  b.wa = Xd(a.v.Hc);
  b.Sb = a.v.$d;
  a.s.push(b);
  a.Ua = b.wa
}
function xe(a, b) {
  b && (a.sa += 0.5);
  a.b()
}
t.aa = function() {
  this.da && !this.Ba && e(Error("flush_: Can't flush more than once to this transport."));
  if(this.gc) {
    V(this.a, this.m() + " flush_: Returning because spinning right now.")
  }else {
    var a = this.da;
    this.da = j;
    !a && !this.s.length && Wf(this);
    for(a = 0;a < this.s.length;a++) {
      U(this.a, this.m() + " SEND " + P(this.s[a]))
    }
    if(this.Sa()) {
      for(var a = [], b = 0, c = this.s.length;b < c;b++) {
        this.s[b].S(a), a.push("\n")
      }
      this.s = [];
      a = a.join("");
      b = this.ha ? this.r.X : this.r.ya;
      this.l = Ff.wc(this, this.ha ? this.r.ne : this.r.we);
      this.kd = this.p.w === Pb ? pa() : this.p.w.getTime();
      this.l.Lc(b, "POST", a);
      Ef(this, 3E3 * (1.5 + (0 == b.indexOf("https://") ? 3 : 1)) + 4E3 + (this.va ? 0 : this.ha ? 25E3 : 0))
    }else {
      if(this.Z == bg) {
        a = [];
        b = 0;
        for(c = this.s.length;b < c;b++) {
          a.push(this.s[b].N())
        }
        this.s = [];
        this.l ? this.l.zb(a) : (b = this.r, this.l = new ze(this), c = b.Jf.wc(this.l), this.l.fc = c, this.kd = this.p.w === Pb ? pa() : this.p.w.getTime(), this.l.tc(b.host, b.port), this.l.$ || (this.l.zb(a), this.l.$ || Ef(this, 8E3)))
      }else {
        e(Error("flush_: Don't know what to do for this transportType: " + this.Z))
      }
    }
  }
};
function Xf(a, b, c) {
  !a.da && !a.s.length && Wf(a);
  for(var d = Math.max(c, a.Xa + 1), g = Ud(b), c = [], f = 0;f < g.length;f++) {
    var i = g[f];
    (d == k || i >= d) && c.push([i, b.G.get(i)[0]])
  }
  b = 0;
  for(d = c.length;b < d;b++) {
    f = c[b], g = f[0], f = f[1], (-1 == a.Xa || a.Xa + 1 != g) && a.s.push(new Ne(g)), a.s.push(new Le(f)), a.Xa = g
  }
}
t.c = function() {
  this.a.info(this.m() + " in disposeInternal.");
  cg.g.c.call(this);
  this.Ge = this.p.w === Pb ? pa() : this.p.w.getTime();
  this.s = [];
  mg(this);
  this.l && this.l.b();
  var a = this.v;
  this.v = k;
  gg(a, this)
};
function ig(a, b) {
  !a.da && !a.s.length && Wf(a);
  a.s.push(new Se(b, j));
  a.Je = j
}
function fg(a, b, c, d) {
  L.call(this);
  this.p = a;
  this.v = b;
  this.yd = c;
  this.ud = d
}
E(fg, L);
t = fg.prototype;
t.da = m;
t.Ba = m;
t.Mb = k;
t.Ua = k;
t.a = W("cw.net.DoNothingTransport");
function ng(a) {
  a.Mb = a.p.w.setTimeout(function() {
    a.Mb = k;
    a.ud--;
    a.ud ? ng(a) : a.b()
  }, a.yd)
}
t.aa = function() {
  this.da && !this.Ba && e(Error("flush_: Can't flush more than once to DoNothingTransport."));
  this.da = j;
  ng(this)
};
t.B = function(a) {
  a.push("<DoNothingTransport delay=", String(this.yd), ">")
};
t.Sa = q(m);
t.m = q("Wast. T");
t.sd = q(m);
t.c = function() {
  this.a.info(this.m() + " in disposeInternal.");
  fg.g.c.call(this);
  this.Mb != k && this.p.w.clearTimeout(this.Mb);
  var a = this.v;
  this.v = k;
  gg(a, this)
};
function og(a) {
  a = String(a);
  if(/^\s*$/.test(a) ? 0 : /^[\],:{}\s\u2028\u2029]*$/.test(a.replace(/\\["\\\/bfnrtu]/g, "@").replace(/"[^"\\\n\r\u2028\u2029\x00-\x08\x10-\x1f]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, "]").replace(/(?:^|:|,)(?:[\s\u2028\u2029]*\[)+/g, ""))) {
    try {
      return eval("(" + a + ")")
    }catch(b) {
    }
  }
  e(Error("Invalid JSON string: " + a))
}
;function pg() {
}
var qg;
ea(pg);
t = pg.prototype;
t.Jb = aa();
t.z = function(a) {
  var b = a.Na().z("div", rg(this, a).join(" "), a.fb);
  sg(this, a, b);
  return b
};
t.gb = function(a, b, c) {
  if(a = a.k ? a.k() : a) {
    if(G && !J("7")) {
      var d = tg(oc(a), b);
      d.push(b);
      oa(c ? pc : qc, a).apply(k, d)
    }else {
      c ? pc(a, b) : qc(a, b)
    }
  }
};
t.Sd = function(a) {
  a.tb == k && (a.tb = "rtl" == Lc(a.T ? a.f : a.Eb.M.body, "direction"));
  a.tb && this.$a(a.k(), j);
  a.isEnabled() && this.cc(a, a.bb)
};
function sg(a, b, c) {
  b.isEnabled() || a.fa(c, 1, j);
  b.e & 8 && a.fa(c, 8, j);
  b.K & 16 && a.fa(c, 16, !!(b.e & 16));
  b.K & 64 && a.fa(c, 64, !!(b.e & 64))
}
t.bc = function(a, b) {
  var c = !b, d = G || Ka ? a.getElementsByTagName("*") : k;
  if(Pc) {
    if(c = c ? "none" : "", a.style[Pc] = c, d) {
      for(var g = 0, f;f = d[g];g++) {
        f.style[Pc] = c
      }
    }
  }else {
    if(G || Ka) {
      if(c = c ? "on" : "", a.setAttribute("unselectable", c), d) {
        for(g = 0;f = d[g];g++) {
          f.setAttribute("unselectable", c)
        }
      }
    }
  }
};
t.$a = function(a, b) {
  this.gb(a, this.oa() + "-rtl", b)
};
t.Wd = function(a) {
  var b;
  return a.K & 32 && (b = a.Da()) ? Hc(b) : m
};
t.cc = function(a, b) {
  var c;
  if(a.K & 32 && (c = a.Da())) {
    if(!b && a.e & 32) {
      try {
        c.blur()
      }catch(d) {
      }
      a.e & 32 && a.Hd()
    }
    Hc(c) != b && (b ? c.tabIndex = 0 : (c.tabIndex = -1, c.removeAttribute("tabIndex")))
  }
};
t.ad = function(a, b) {
  a.style.display = b ? "" : "none"
};
t.R = function(a, b, c) {
  var d = a.k();
  if(d) {
    var g = ug(this, b);
    g && this.gb(a, g, c);
    this.fa(d, b, c)
  }
};
t.fa = function(a, b, c) {
  qg || (qg = {1:"disabled", 8:"selected", 16:"checked", 64:"expanded"});
  (b = qg[b]) && a.setAttribute("aria-" + b, c)
};
t.Da = function(a) {
  return a.k()
};
t.oa = q("goog-control");
function rg(a, b) {
  var c = a.oa(), d = [c], g = a.oa();
  g != c && d.push(g);
  c = b.e;
  for(g = [];c;) {
    var f = c & -c;
    g.push(ug(a, f));
    c &= ~f
  }
  d.push.apply(d, g);
  (c = b.V) && d.push.apply(d, c);
  G && !J("7") && d.push.apply(d, tg(d));
  return d
}
function tg(a, b) {
  var c = [];
  b && (a = a.concat([b]));
  hb([], function(d) {
    lb(d, oa(mb, a)) && (!b || mb(d, b)) && c.push(d.join("_"))
  });
  return c
}
function ug(a, b) {
  if(!a.rd) {
    var c = a.oa();
    a.rd = {1:c + "-disabled", 2:c + "-hover", 4:c + "-active", 8:c + "-selected", 16:c + "-checked", 32:c + "-focused", 64:c + "-open"}
  }
  return a.rd[b]
}
;function vg(a, b) {
  a || e(Error("Invalid class name " + a));
  z(b) || e(Error("Invalid decorator function " + b))
}
var wg = {};
function xg(a, b, c, d, g) {
  if(!G && (!I || !J("525"))) {
    return j
  }
  if(Ma && g) {
    return yg(a)
  }
  if(g && !d || !c && (17 == b || 18 == b || Ma && 91 == b)) {
    return m
  }
  if(I && d && c) {
    switch(a) {
      case 220:
      ;
      case 219:
      ;
      case 221:
      ;
      case 192:
      ;
      case 186:
      ;
      case 189:
      ;
      case 187:
      ;
      case 188:
      ;
      case 190:
      ;
      case 191:
      ;
      case 192:
      ;
      case 222:
        return m
    }
  }
  if(G && d && b == a) {
    return m
  }
  switch(a) {
    case 13:
      return!(G && Wa(9));
    case 27:
      return!I
  }
  return yg(a)
}
function yg(a) {
  if(48 <= a && 57 >= a || 96 <= a && 106 >= a || 65 <= a && 90 >= a || I && 0 == a) {
    return j
  }
  switch(a) {
    case 32:
    ;
    case 63:
    ;
    case 107:
    ;
    case 109:
    ;
    case 110:
    ;
    case 111:
    ;
    case 186:
    ;
    case 59:
    ;
    case 189:
    ;
    case 187:
    ;
    case 61:
    ;
    case 188:
    ;
    case 190:
    ;
    case 191:
    ;
    case 192:
    ;
    case 222:
    ;
    case 219:
    ;
    case 220:
    ;
    case 221:
      return j;
    default:
      return m
  }
}
function zg(a) {
  switch(a) {
    case 61:
      return 187;
    case 59:
      return 186;
    case 224:
      return 91;
    case 0:
      return 224;
    default:
      return a
  }
}
;function Ag(a, b) {
  L.call(this);
  a && Bg(this, a, b)
}
E(Ag, Ob);
t = Ag.prototype;
t.f = k;
t.Qb = k;
t.Ic = k;
t.Rb = k;
t.H = -1;
t.qa = -1;
t.oc = m;
var Cg = {3:13, 12:144, 63232:38, 63233:40, 63234:37, 63235:39, 63236:112, 63237:113, 63238:114, 63239:115, 63240:116, 63241:117, 63242:118, 63243:119, 63244:120, 63245:121, 63246:122, 63247:123, 63248:44, 63272:46, 63273:36, 63275:35, 63276:33, 63277:34, 63289:144, 63302:45}, Dg = {Up:38, Down:40, Left:37, Right:39, Enter:13, F1:112, F2:113, F3:114, F4:115, F5:116, F6:117, F7:118, F8:119, F9:120, F10:121, F11:122, F12:123, "U+007F":46, Home:36, End:35, PageUp:33, PageDown:34, Insert:45}, Eg = G || 
I && J("525"), Fg = Ma && H;
t = Ag.prototype;
t.ff = function(a) {
  I && (17 == this.H && !a.ctrlKey || 18 == this.H && !a.altKey || Ma && 91 == this.H && !a.metaKey ? this.qa = this.H = -1 : -1 == this.H && (a.ctrlKey && 17 != a.keyCode ? this.H = 17 : a.altKey && 18 != a.keyCode ? this.H = 18 : a.metaKey && 91 != a.keyCode && (this.H = 91)));
  Eg && !xg(a.keyCode, this.H, a.shiftKey, a.ctrlKey, a.altKey) ? this.handleEvent(a) : (this.qa = H ? zg(a.keyCode) : a.keyCode, Fg && (this.oc = a.altKey))
};
t.hf = function(a) {
  this.qa = this.H = -1;
  this.oc = a.altKey
};
t.handleEvent = function(a) {
  var b = a.ma, c, d, g = b.altKey;
  G && "keypress" == a.type ? (c = this.qa, d = 13 != c && 27 != c ? b.keyCode : 0) : I && "keypress" == a.type ? (c = this.qa, d = 0 <= b.charCode && 63232 > b.charCode && yg(c) ? b.charCode : 0) : Ka ? (c = this.qa, d = yg(c) ? b.keyCode : 0) : (c = b.keyCode || this.qa, d = b.charCode || 0, Fg && (g = this.oc), Ma && (63 == d && 224 == c) && (c = 191));
  var f = c, i = b.keyIdentifier;
  c ? 63232 <= c && c in Cg ? f = Cg[c] : 25 == c && a.shiftKey && (f = 9) : i && i in Dg && (f = Dg[i]);
  a = f == this.H;
  this.H = f;
  b = new Gg(f, d, a, b);
  b.altKey = g;
  this.dispatchEvent(b)
};
t.k = p("f");
function Bg(a, b, c) {
  a.Rb && a.detach();
  a.f = b;
  a.Qb = N(a.f, "keypress", a, c);
  a.Ic = N(a.f, "keydown", a.ff, c, a);
  a.Rb = N(a.f, "keyup", a.hf, c, a)
}
t.detach = function() {
  this.Qb && (Jb(this.Qb), Jb(this.Ic), Jb(this.Rb), this.Rb = this.Ic = this.Qb = k);
  this.f = k;
  this.qa = this.H = -1
};
t.c = function() {
  Ag.g.c.call(this);
  this.detach()
};
function Gg(a, b, c, d) {
  d && this.mb(d, h);
  this.type = "key";
  this.keyCode = a;
  this.charCode = b;
  this.repeat = c
}
E(Gg, zb);
function Z(a, b, c) {
  Uc.call(this, c);
  if(!b) {
    for(var b = this.constructor, d;b;) {
      d = B(b);
      if(d = wg[d]) {
        break
      }
      b = b.g ? b.g.constructor : k
    }
    b = d ? z(d.Oa) ? d.Oa() : new d : k
  }
  this.u = b;
  this.fb = a
}
E(Z, Uc);
t = Z.prototype;
t.fb = k;
t.e = 0;
t.K = 39;
t.pc = 255;
t.Ef = 0;
t.bb = j;
t.V = k;
t.Ec = j;
t.nc = m;
t.uf = k;
t.Da = function() {
  return this.u.Da(this)
};
function Hg(a, b) {
  b && (a.V ? mb(a.V, b) || a.V.push(b) : a.V = [b], a.u.gb(a, b, j))
}
t.gb = function(a, b) {
  b ? Hg(this, a) : a && this.V && (nb(this.V, a), 0 == this.V.length && (this.V = k), this.u.gb(this, a, m))
};
t.z = function() {
  var a = this.u.z(this);
  this.f = a;
  var b = this.uf || this.u.Jb();
  b && a.setAttribute("role", b);
  this.nc || this.u.bc(a, m);
  this.bb || this.u.ad(a, m)
};
t.la = function() {
  Z.g.la.call(this);
  this.u.Sd(this);
  if(this.K & -2 && (this.Ec && Ig(this, j), this.K & 32)) {
    var a = this.Da();
    if(a) {
      var b = this.Ta || (this.Ta = new Ag);
      Bg(b, a);
      R(R(R(Yc(this), b, "key", this.gf), a, "focus", this.ef), a, "blur", this.Hd)
    }
  }
};
function Ig(a, b) {
  var c = Yc(a), d = a.k();
  b ? (R(R(R(R(c, d, "mouseover", a.Md), d, "mousedown", a.Kd), d, "mouseup", a.Nd), d, "mouseout", a.Ld), a.Nb != v && R(c, d, "contextmenu", a.Nb), G && R(c, d, "dblclick", a.Jd)) : (Sc(Sc(Sc(Sc(c, d, "mouseover", a.Md), d, "mousedown", a.Kd), d, "mouseup", a.Nd), d, "mouseout", a.Ld), a.Nb != v && Sc(c, d, "contextmenu", a.Nb), G && Sc(c, d, "dblclick", a.Jd))
}
t.hb = function() {
  Z.g.hb.call(this);
  this.Ta && this.Ta.detach();
  this.bb && this.isEnabled() && this.u.cc(this, m)
};
t.c = function() {
  Z.g.c.call(this);
  this.Ta && (this.Ta.b(), delete this.Ta);
  delete this.u;
  this.V = this.fb = k
};
function Jg(a) {
  a = a.fb;
  if(!a) {
    return""
  }
  if(!x(a)) {
    if(ga(a)) {
      a = jb(a, Ic).join("")
    }else {
      if(tc && "innerText" in a) {
        a = a.innerText.replace(/(\r\n|\r|\n)/g, "\n")
      }else {
        var b = [];
        Jc(a, b, j);
        a = b.join("")
      }
      a = a.replace(/ \xAD /g, " ").replace(/\xAD/g, "");
      a = a.replace(/\u200B/g, "");
      tc || (a = a.replace(/ +/g, " "));
      " " != a && (a = a.replace(/^\s*/, ""))
    }
  }
  return a.replace(/[\t\r\n ]+/g, " ").replace(/^[\t\r\n ]+|[\t\r\n ]+$/g, "")
}
t.$a = function(a) {
  Z.g.$a.call(this, a);
  var b = this.k();
  b && this.u.$a(b, a)
};
t.bc = function(a) {
  this.nc = a;
  var b = this.k();
  b && this.u.bc(b, a)
};
t.ad = function(a, b) {
  if(b || this.bb != a && this.dispatchEvent(a ? "show" : "hide")) {
    var c = this.k();
    c && this.u.ad(c, a);
    this.isEnabled() && this.u.cc(this, a);
    this.bb = a;
    return j
  }
  return m
};
t.isEnabled = function() {
  return!(this.e & 1)
};
function Kg(a, b) {
  Lg(a, 2, b) && a.R(2, b)
}
t.Ud = function() {
  return!!(this.e & 4)
};
t.setActive = function(a) {
  Lg(this, 4, a) && this.R(4, a)
};
t.R = function(a, b) {
  this.K & a && b != !!(this.e & a) && (this.u.R(this, a, b), this.e = b ? this.e | a : this.e & ~a)
};
function $(a, b) {
  return!!(a.pc & b) && !!(a.K & b)
}
function Lg(a, b, c) {
  return!!(a.K & b) && !!(a.e & b) != c && (!(a.Ef & b) || a.dispatchEvent(Wc(b, c))) && !a.$
}
t.Md = function(a) {
  (!a.relatedTarget || !Dc(this.k(), a.relatedTarget)) && (this.dispatchEvent("enter") && this.isEnabled() && $(this, 2)) && Kg(this, j)
};
t.Ld = function(a) {
  if((!a.relatedTarget || !Dc(this.k(), a.relatedTarget)) && this.dispatchEvent("leave")) {
    $(this, 4) && this.setActive(m), $(this, 2) && Kg(this, m)
  }
};
t.Nb = v;
t.Kd = function(a) {
  if(this.isEnabled() && ($(this, 2) && Kg(this, j), Bb(a) && (!I || !Ma || !a.ctrlKey))) {
    $(this, 4) && this.setActive(j), this.u.Wd(this) && this.Da().focus()
  }
  !this.nc && (Bb(a) && (!I || !Ma || !a.ctrlKey)) && a.preventDefault()
};
t.Nd = function(a) {
  this.isEnabled() && ($(this, 2) && Kg(this, j), this.Ud() && (this.qb(a) && $(this, 4)) && this.setActive(m))
};
t.Jd = function(a) {
  this.isEnabled() && this.qb(a)
};
t.qb = function(a) {
  if($(this, 16)) {
    var b = !(this.e & 16);
    Lg(this, 16, b) && this.R(16, b)
  }
  $(this, 8) && Lg(this, 8, j) && this.R(8, j);
  $(this, 64) && (b = !(this.e & 64), Lg(this, 64, b) && this.R(64, b));
  b = new wb("action", this);
  a && (b.altKey = a.altKey, b.ctrlKey = a.ctrlKey, b.metaKey = a.metaKey, b.shiftKey = a.shiftKey, b.Vc = a.Vc);
  return this.dispatchEvent(b)
};
t.ef = function() {
  $(this, 32) && Lg(this, 32, j) && this.R(32, j)
};
t.Hd = function() {
  $(this, 4) && this.setActive(m);
  $(this, 32) && Lg(this, 32, m) && this.R(32, m)
};
t.gf = function(a) {
  return this.bb && this.isEnabled() && this.Dc(a) ? (a.preventDefault(), a.stopPropagation(), j) : m
};
t.Dc = function(a) {
  return 13 == a.keyCode && this.qb(a)
};
z(Z) || e(Error("Invalid component class " + Z));
z(pg) || e(Error("Invalid renderer class " + pg));
var Mg = B(Z);
wg[Mg] = pg;
vg("goog-control", function() {
  return new Z(k)
});
function Ng() {
}
E(Ng, pg);
ea(Ng);
t = Ng.prototype;
t.Jb = q("button");
t.fa = function(a, b, c) {
  16 == b ? a.setAttribute("aria-pressed", c) : Ng.g.fa.call(this, a, b, c)
};
t.z = function(a) {
  var b = Ng.g.z.call(this, a), c = a.Kb();
  c && this.$c(b, c);
  (c = a.Lb()) && this.ec(b, c);
  a.K & 16 && this.fa(b, 16, !!(a.e & 16));
  return b
};
t.Lb = v;
t.ec = v;
t.Kb = function(a) {
  return a.title
};
t.$c = function(a, b) {
  a && (a.title = b || "")
};
t.oa = q("goog-button");
function Og() {
}
E(Og, Ng);
ea(Og);
t = Og.prototype;
t.Jb = aa();
t.z = function(a) {
  a.T && m != a.Ec && Ig(a, m);
  a.Ec = m;
  a.pc &= -256;
  a.T && a.e & 32 && e(Error("Component already rendered"));
  a.e & 32 && a.R(32, m);
  a.K &= -33;
  return a.Na().z("button", {"class":rg(this, a).join(" "), disabled:!a.isEnabled(), title:a.Kb() || "", value:a.Lb() || ""}, Jg(a) || "")
};
t.Sd = function(a) {
  R(Yc(a), a.k(), "click", a.qb)
};
t.bc = v;
t.$a = v;
t.Wd = function(a) {
  return a.isEnabled()
};
t.cc = v;
t.R = function(a, b, c) {
  Og.g.R.call(this, a, b, c);
  if((a = a.k()) && 1 == b) {
    a.disabled = c
  }
};
t.Lb = function(a) {
  return a.value
};
t.ec = function(a, b) {
  a && (a.value = b)
};
t.fa = v;
function Pg(a, b, c) {
  Z.call(this, a, b || Og.Oa(), c)
}
E(Pg, Z);
t = Pg.prototype;
t.Lb = p("Ie");
t.ec = function(a) {
  this.Ie = a;
  this.u.ec(this.k(), a)
};
t.Kb = p("Fe");
t.$c = function(a) {
  this.Fe = a;
  this.u.$c(this.k(), a)
};
t.c = function() {
  Pg.g.c.call(this);
  delete this.Ie;
  delete this.Fe
};
t.la = function() {
  Pg.g.la.call(this);
  if(this.K & 32) {
    var a = this.Da();
    a && R(Yc(this), a, "keyup", this.Dc)
  }
};
t.Dc = function(a) {
  return 13 == a.keyCode && "key" == a.type || 32 == a.keyCode && "keyup" == a.type ? this.qb(a) : 32 == a.keyCode
};
vg("goog-button", function() {
  return new Pg(k)
});
function Qg() {
}
E(Qg, Ng);
ea(Qg);
Qg.prototype.z = function(a) {
  var b = {"class":"goog-inline-block " + rg(this, a).join(" "), title:a.Kb() || ""}, b = a.Na().z("div", b, Rg(this, a.fb, a.Na()));
  sg(this, a, b);
  return b
};
Qg.prototype.Jb = q("button");
function Rg(a, b, c) {
  return c.z("div", "goog-inline-block " + (a.oa() + "-outer-box"), c.z("div", "goog-inline-block " + (a.oa() + "-inner-box"), b))
}
Qg.prototype.oa = q("goog-custom-button");
function Sg(a, b, c) {
  Pg.call(this, a, b || Qg.Oa(), c)
}
E(Sg, Pg);
vg("goog-custom-button", function() {
  return new Sg(k)
});
function Tg() {
}
Tg.prototype.Ab = k;
var Ug;
function Vg() {
}
E(Vg, Tg);
function Wg(a) {
  return(a = Xg(a)) ? new ActiveXObject(a) : new XMLHttpRequest
}
function Yg(a) {
  var b = {};
  Xg(a) && (b[0] = j, b[1] = j);
  return b
}
function Xg(a) {
  if(!a.Rd && "undefined" == typeof XMLHttpRequest && "undefined" != typeof ActiveXObject) {
    for(var b = ["MSXML2.XMLHTTP.6.0", "MSXML2.XMLHTTP.3.0", "MSXML2.XMLHTTP", "Microsoft.XMLHTTP"], c = 0;c < b.length;c++) {
      var d = b[c];
      try {
        return new ActiveXObject(d), a.Rd = d
      }catch(g) {
      }
    }
    e(Error("Could not create ActiveXObject. ActiveX might be disabled, or MSXML might not be installed"))
  }
  return a.Rd
}
Ug = new Vg;
function Zg(a) {
  L.call(this);
  this.headers = new ld;
  this.cb = a || k
}
E(Zg, Ob);
Zg.prototype.a = W("goog.net.XhrIo");
var $g = /^https?$/i;
t = Zg.prototype;
t.ga = m;
t.i = k;
t.kc = k;
t.Tb = "";
t.Yd = "";
t.nb = 0;
t.ob = "";
t.yc = m;
t.Pb = m;
t.Gc = m;
t.Ea = m;
t.hc = 0;
t.Ka = k;
t.ue = "";
t.Pf = m;
t.send = function(a, b, c, d) {
  this.i && e(Error("[goog.net.XhrIo] Object is active with another request=" + this.Tb + "; newUri=" + a));
  b = b ? b.toUpperCase() : "GET";
  this.Tb = a;
  this.ob = "";
  this.nb = 0;
  this.Yd = b;
  this.yc = m;
  this.ga = j;
  this.i = this.cb ? Wg(this.cb) : Wg(Ug);
  this.kc = this.cb ? this.cb.Ab || (this.cb.Ab = Yg(this.cb)) : Ug.Ab || (Ug.Ab = Yg(Ug));
  this.i.onreadystatechange = C(this.ke, this);
  try {
    U(this.a, ah(this, "Opening Xhr")), this.Gc = j, this.i.open(b, a, j), this.Gc = m
  }catch(g) {
    U(this.a, ah(this, "Error opening Xhr: " + g.message));
    bh(this, g);
    return
  }
  var a = c || "", f = this.headers.L();
  d && jd(d, function(a, b) {
    f.set(b, a)
  });
  d = u.FormData && a instanceof u.FormData;
  "POST" == b && (!f.ja("Content-Type") && !d) && f.set("Content-Type", "application/x-www-form-urlencoded;charset=utf-8");
  jd(f, function(a, b) {
    this.i.setRequestHeader(b, a)
  }, this);
  this.ue && (this.i.responseType = this.ue);
  "withCredentials" in this.i && (this.i.withCredentials = this.Pf);
  try {
    this.Ka && (Pb.clearTimeout(this.Ka), this.Ka = k), 0 < this.hc && (U(this.a, ah(this, "Will abort after " + this.hc + "ms if incomplete")), this.Ka = Pb.setTimeout(C(this.If, this), this.hc)), U(this.a, ah(this, "Sending request")), this.Pb = j, this.i.send(a), this.Pb = m
  }catch(i) {
    U(this.a, ah(this, "Send error: " + i.message)), bh(this, i)
  }
};
t.If = function() {
  "undefined" != typeof ca && this.i && (this.ob = "Timed out after " + this.hc + "ms, aborting", this.nb = 8, U(this.a, ah(this, this.ob)), this.dispatchEvent("timeout"), this.abort(8))
};
function bh(a, b) {
  a.ga = m;
  a.i && (a.Ea = j, a.i.abort(), a.Ea = m);
  a.ob = b;
  a.nb = 5;
  ch(a);
  dh(a)
}
function ch(a) {
  a.yc || (a.yc = j, a.dispatchEvent("complete"), a.dispatchEvent("error"))
}
t.abort = function(a) {
  this.i && this.ga && (U(this.a, ah(this, "Aborting")), this.ga = m, this.Ea = j, this.i.abort(), this.Ea = m, this.nb = a || 7, this.dispatchEvent("complete"), this.dispatchEvent("abort"), dh(this))
};
t.c = function() {
  this.i && (this.ga && (this.ga = m, this.Ea = j, this.i.abort(), this.Ea = m), dh(this, j));
  Zg.g.c.call(this)
};
t.ke = function() {
  !this.Gc && !this.Pb && !this.Ea ? this.tf() : eh(this)
};
t.tf = function() {
  eh(this)
};
function eh(a) {
  if(a.ga && "undefined" != typeof ca) {
    if(a.kc[1] && 4 == a.pa() && 2 == fh(a)) {
      U(a.a, ah(a, "Local request error detected and ignored"))
    }else {
      if(a.Pb && 4 == a.pa()) {
        Pb.setTimeout(C(a.ke, a), 0)
      }else {
        if(a.dispatchEvent("readystatechange"), 4 == a.pa()) {
          U(a.a, ah(a, "Request complete"));
          a.ga = m;
          try {
            var b = fh(a), c;
            a: {
              switch(b) {
                case 200:
                ;
                case 201:
                ;
                case 202:
                ;
                case 204:
                ;
                case 206:
                ;
                case 304:
                ;
                case 1223:
                  c = j;
                  break a;
                default:
                  c = m
              }
            }
            var d;
            if(!(d = c)) {
              var g;
              if(g = 0 === b) {
                var f = String(a.Tb).match(We)[1] || k;
                if(!f && self.location) {
                  var i = self.location.protocol, f = i.substr(0, i.length - 1)
                }
                g = !$g.test(f ? f.toLowerCase() : "")
              }
              d = g
            }
            if(d) {
              a.dispatchEvent("complete"), a.dispatchEvent("success")
            }else {
              a.nb = 6;
              var l;
              try {
                l = 2 < a.pa() ? a.i.statusText : ""
              }catch(n) {
                U(a.a, "Can not get status: " + n.message), l = ""
              }
              a.ob = l + " [" + fh(a) + "]";
              ch(a)
            }
          }finally {
            dh(a)
          }
        }
      }
    }
  }
}
function dh(a, b) {
  if(a.i) {
    var c = a.i, d = a.kc[0] ? v : k;
    a.i = k;
    a.kc = k;
    a.Ka && (Pb.clearTimeout(a.Ka), a.Ka = k);
    b || a.dispatchEvent("ready");
    try {
      c.onreadystatechange = d
    }catch(g) {
      S(a.a, "Problem encountered resetting onreadystatechange: " + g.message)
    }
  }
}
t.Ud = function() {
  return!!this.i
};
t.pa = function() {
  return this.i ? this.i.readyState : 0
};
function fh(a) {
  try {
    return 2 < a.pa() ? a.i.status : -1
  }catch(b) {
    return T(a.a, "Can not get status: " + b.message), -1
  }
}
t.getResponseHeader = function(a) {
  return this.i && 4 == this.pa() ? this.i.getResponseHeader(a) : h
};
function ah(a, b) {
  return b + " [" + a.Yd + " " + a.Tb + " " + fh(a) + "]"
}
;var gh = !(G || I && !J("420+"));
function hh(a, b) {
  this.ic = a;
  this.U = b
}
E(hh, L);
t = hh.prototype;
t.l = k;
t.ua = -1;
t.Gd = m;
t.Pd = "Content-Length Server Date Expires Keep-Alive Content-Type Transfer-Encoding Cache-Control".split(" ");
function ih(a) {
  var b = Bf(a.wd), c = b[0], b = b[1], d = u.parent;
  d ? (d.__XHRMaster_onframes(a.U, c, b), 1 != b && a.b()) : a.b()
}
t.jf = function() {
  ih(this);
  if(!this.$) {
    var a = u.parent;
    a && a.__XHRMaster_oncomplete(this.U);
    this.b()
  }
};
t.xf = function() {
  var a = u.parent;
  if(a) {
    this.ua = this.l.pa();
    if(2 <= this.ua && !this.Gd) {
      for(var b = new ld, c = this.Pd.length;c--;) {
        var d = this.Pd[c];
        try {
          b.set(d, this.l.i.getResponseHeader(d))
        }catch(g) {
        }
      }
      if(b.F() && (this.Gd = j, a.__XHRMaster_ongotheaders(this.U, pd(b)), this.$)) {
        return
      }
    }
    a.__XHRMaster_onreadystatechange(this.U, this.ua);
    gh && 3 == this.ua && ih(this)
  }else {
    this.b()
  }
};
t.Lc = function(a, b, c) {
  this.l = new Zg;
  N(this.l, "readystatechange", C(this.xf, this));
  N(this.l, "complete", C(this.jf, this));
  this.l.send(a + "io/", b, c, {"Content-Type":"application/octet-stream"});
  this.wd = new Af(this.l.i, 1048576)
};
t.c = function() {
  hh.g.c.call(this);
  delete this.wd;
  this.l && this.l.b();
  delete this.ic.ub[this.U];
  delete this.ic
};
function jh() {
  L.call(this);
  this.ub = {}
}
E(jh, L);
jh.prototype.nf = function(a, b, c, d) {
  var g = new hh(this, a);
  this.ub[a] = g;
  g.Lc(b, c, d)
};
jh.prototype.Xe = function(a) {
  (a = this.ub[a]) && a.b()
};
jh.prototype.c = function() {
  jh.g.c.call(this);
  for(var a = $a(this.ub);a.length;) {
    a.pop().b()
  }
  delete this.ub
};
var kh = new jh;
u.__XHRSlave_makeRequest = C(kh.nf, kh);
u.__XHRSlave_dispose = C(kh.Xe, kh);
var lh = W("cw.net.demo");
function mh() {
}
mh.prototype.Fd = function() {
  return Boolean(Number((new Ye(document.location)).I.get("httpStreaming", "0"))) ? 2 : 1
};
var nh = W("bskystream.logger");
window.onerror = function(a, b, c) {
  S(nh, "window.onerror: message: " + P(a) + "\nURL: " + b + "\nLine Number: " + c)
};
function oh() {
}
oh.prototype.Be = function(a) {
  this.v = a;
  $f(this.v, "subprotocol:bskystream");
  ph(this)
};
oh.prototype.Ae = function(a, b) {
  nh.info("streamReset: reasonString=" + P(a) + ", applicationLevel=" + b);
  qh("Disconnected from server.  Try reloading this page.");
  rh = k
};
oh.prototype.Ce = function(a) {
  var b = og(a), a = b[1];
  "NewPost" == b[0] ? (b = zc("span", {}, zc("a", {href:a.url, "class":"post-author", target:"_blank", rel:"noopener noreferrer"}, "@" + a.handle), " ", zc("span", {"class":"post-text"}, a.text)), a.media && Cc(b, " ", zc("span", {"class":"post-media"}, "[" + a.media + "]")), a.langs.length && Cc(b, " ", zc("span", {"class":"post-langs"}, a.langs.join(", "))), sh(b)) : T(nh, "Strange message from server: " + P(b))
};
function ph(a) {
  var b = Q("language").value || k;
  nh.info("Sending preferences to server: language=" + P(b));
  $f(a.v, dc(["SetPreferences", {language:b}]))
}
oh.prototype.reset = function(a) {
  nh.info("resetting with reason: " + a);
  this.v.reset(a)
};
var rh = k, th = new ac(u.window);
function qh(a) {
  sh(zc("span", {"class":"important-message"}, a))
}
function uh() {
  rh && (rh.reset("idle timeout fired"), rh = k, qh("No key/mouse activity, stopping stream to save everyone's bandwidth."))
}
var vh = k;
function wh() {
  vh != k && th.w.clearTimeout(vh);
  rh && (vh = th.w.setTimeout(uh, 6E5))
}
N(window, ["click", "focus", "keydown", "keypress"], wh, j);
var xh = new vc, yh = 0, zh = j;
function sh(a) {
  var a = zc("div", {"class":"row-" + (0 == yh % 2 ? "even" : "odd")}, a), b = Q("bskystream-container");
  b.appendChild(a);
  for(yh += 1;1E3 < b.childNodes.length;) {
    b.removeChild(b.firstChild)
  }
  if(b = zh) {
    var c, d = wc(a), g = Lc(a, "position"), f = H && d.getBoxObjectFor && !a.getBoundingClientRect && "absolute" == g && (c = d.getBoxObjectFor(a)) && (0 > c.screenX || 0 > c.screenY), b = new lc(0, 0), i;
    c = d ? wc(d) : document;
    if(i = G) {
      if(i = !Wa(9)) {
        i = "CSS1Compat" != uc(c).M.compatMode
      }
    }
    i = i ? c.body : c.documentElement;
    if(a != i) {
      if(a.getBoundingClientRect) {
        c = a.getBoundingClientRect(), G && (g = a.ownerDocument, c.left -= g.documentElement.clientLeft + g.body.clientLeft, c.top -= g.documentElement.clientTop + g.body.clientTop), d = uc(d), d = yc(d.M), b.x = c.left + d.x, b.y = c.top + d.y
      }else {
        if(d.getBoxObjectFor && !f) {
          c = d.getBoxObjectFor(a), d = d.getBoxObjectFor(i), b.x = c.screenX - d.screenX, b.y = c.screenY - d.screenY
        }else {
          c = a;
          do {
            b.x += c.offsetLeft;
            b.y += c.offsetTop;
            c != a && (b.x += c.clientLeft || 0, b.y += c.clientTop || 0);
            if(I && "fixed" == Lc(c, "position")) {
              b.x += d.body.scrollLeft;
              b.y += d.body.scrollTop;
              break
            }
            c = c.offsetParent
          }while(c && c != a);
          if(Ka || I && "absolute" == g) {
            b.y -= d.body.offsetTop
          }
          for(c = a;(c = Mc(c)) && c != d.body && c != i;) {
            if(b.x -= c.scrollLeft, !Ka || "TR" != c.tagName) {
              b.y -= c.scrollTop
            }
          }
        }
      }
    }
    c = (xh.M.parentWindow || xh.M.defaultView || window).document;
    c = "CSS1Compat" == c.compatMode ? c.documentElement : c.body;
    b = !(b.y + a.offsetHeight <= yc(document).y + (new mc(c.clientWidth, c.clientHeight)).height)
  }
  b && a.scrollIntoView(m)
}
function Ah() {
  Q("bskystream-container").style.marginTop = Q("demo-header").offsetHeight + "px"
}
function Bh() {
  if("1" == (new Ye(document.location)).I.get("logging")) {
    Nd().dc(Id);
    var a = new Od(Q("log"));
    if(j != a.Vd) {
      var b = Nd(), c = a.wf;
      b.lb || (b.lb = []);
      b.lb.push(c);
      a.Vd = j
    }
  }else {
    Nd().dc(Ad)
  }
  nh.info("Logger works.");
  N(Q("language"), "change", function() {
    rh && ph(rh)
  });
  N(Q("automatic_scroll"), "click", function(a) {
    zh = a.target.checked
  });
  a = new Sg("Clear posts");
  Hg(a, "clear-posts-button");
  Zc(a, Q("prefs"));
  N(a, "action", function() {
    for(var a = Q("bskystream-container"), b;b = a.firstChild;) {
      a.removeChild(b)
    }
    window.scrollTo(0, 0)
  });
  Ah();
  N(window, "resize", Ah);
  a = new mh;
  rh = new oh;
  wh();
  c = (new Ye(document.location)).I;
  b = "http" != c.get("mode");
  if((c = Boolean(Number(c.get("useSubdomains", "0")))) && !u.__demo_shared_domain) {
    T(lh, "You requested subdomains, but I cannot use them because you did not specify a domain.  Proceeding without subdomains."), c = m
  }
  var d = c, c = new Ye(document.location);
  b ? b = new Hf("/_minerva/", c.ka, u.__demo_mainSocketPort) : (d ? (b = u.__demo_shared_domain, x(b) || e(Error("domain was " + P(b) + "; expected a string.")), c = c.L(), af(c, "_____random_____." + b)) : c = c.L(), cf(c, "/_minerva/"), df(c, "", h), b = new Lf(c.toString().replace("_____random_____", "%random%")));
  a = new Sf(b, a, th);
  b = rh;
  w(b.Be) || e(Error("Protocol is missing required method streamStarted"));
  w(b.Ae) || e(Error("Protocol is missing required method streamReset"));
  w(b.Ce) || e(Error("Protocol is missing required method stringReceived"));
  a.Rc = C(b.Be, b);
  a.onreset = C(b.Ae, b);
  a.Sc = C(b.Ce, b);
  a.Tc = w(b.Kf) ? C(b.Kf, b) : k;
  a.Uc = w(b.Lf) ? C(b.Lf, b) : k;
  a.start()
}
var Ch = ["__bskystream_init"], Dh = u;
!(Ch[0] in Dh) && Dh.execScript && Dh.execScript("var " + Ch[0]);
for(var Eh;Ch.length && (Eh = Ch.shift());) {
  !Ch.length && w(Bh) ? Dh[Eh] = Bh : Dh = Dh[Eh] ? Dh[Eh] : Dh[Eh] = {}
}
;
})();

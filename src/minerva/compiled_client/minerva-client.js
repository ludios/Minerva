(function() {
function f(a) {
  throw a;
}
var i = void 0, j = !0, k = null, m = !1;
function aa(a) {
  return function(b) {
    this[a] = b
  }
}
function p(a) {
  return function() {
    return this[a]
  }
}
function ba(a) {
  return function() {
    return a
  }
}
var q;
var ca = ca || {}, t = this;
function da(a) {
  a = a.split(".");
  for(var b = t, c;c = a.shift();) {
    if(b[c] != k) {
      b = b[c]
    }else {
      return k
    }
  }
  return b
}
function ea() {
}
function u(a) {
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
function v(a) {
  return a !== i
}
function fa(a) {
  return"array" == u(a)
}
function ga(a) {
  var b = u(a);
  return"array" == b || "object" == b && "number" == typeof a.length
}
function ha(a) {
  return ia(a) && "function" == typeof a.getFullYear
}
function w(a) {
  return"string" == typeof a
}
function ja(a) {
  return"function" == u(a)
}
function ia(a) {
  var b = typeof a;
  return"object" == b && a != k || "function" == b
}
function y(a) {
  return a[ka] || (a[ka] = ++la)
}
var ka = "closure_uid_" + Math.floor(2147483648 * Math.random()).toString(36), la = 0;
function ma(a, b, c) {
  return a.call.apply(a.bind, arguments)
}
function na(a, b, c) {
  a || f(Error());
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
function z(a, b, c) {
  z = Function.prototype.bind && -1 != Function.prototype.bind.toString().indexOf("native code") ? ma : na;
  return z.apply(k, arguments)
}
var oa = Date.now || function() {
  return+new Date
};
function A(a, b) {
  var c = a.split("."), d = t;
  !(c[0] in d) && d.execScript && d.execScript("var " + c[0]);
  for(var g;c.length && (g = c.shift());) {
    !c.length && v(b) ? d[g] = b : d = d[g] ? d[g] : d[g] = {}
  }
}
function C(a, b) {
  function c() {
  }
  c.prototype = b.prototype;
  a.n = b.prototype;
  a.prototype = new c;
  a.prototype.constructor = a
}
;function D(a) {
  Error.captureStackTrace ? Error.captureStackTrace(this, D) : this.stack = Error().stack || "";
  a && (this.message = String(a))
}
C(D, Error);
D.prototype.name = "CustomError";
function pa(a, b) {
  for(var c = 1;c < arguments.length;c++) {
    var d = String(arguments[c]).replace(/\$/g, "$$$$");
    a = a.replace(/\%s/, d)
  }
  return a
}
function qa(a, b) {
  return a.replace(/(\r\n|\r|\n)/g, b ? "<br />" : "<br>")
}
function E(a) {
  if(!ra.test(a)) {
    return a
  }
  -1 != a.indexOf("&") && (a = a.replace(sa, "&amp;"));
  -1 != a.indexOf("<") && (a = a.replace(ta, "&lt;"));
  -1 != a.indexOf(">") && (a = a.replace(ua, "&gt;"));
  -1 != a.indexOf('"') && (a = a.replace(va, "&quot;"));
  return a
}
var sa = /&/g, ta = /</g, ua = />/g, va = /\"/g, ra = /[&<>\"]/;
function wa(a) {
  return qa(a.replace(/  /g, " &#160;"), i)
}
function xa(a, b) {
  for(var c = 0, d = String(a).replace(/^[\s\xa0]+|[\s\xa0]+$/g, "").split("."), g = String(b).replace(/^[\s\xa0]+|[\s\xa0]+$/g, "").split("."), e = Math.max(d.length, g.length), h = 0;0 == c && h < e;h++) {
    var l = d[h] || "", n = g[h] || "", s = RegExp("(\\d*)(\\D*)", "g"), B = RegExp("(\\d*)(\\D*)", "g");
    do {
      var r = s.exec(l) || ["", "", ""], x = B.exec(n) || ["", "", ""];
      if(0 == r[0].length && 0 == x[0].length) {
        break
      }
      c = ((0 == r[1].length ? 0 : parseInt(r[1], 10)) < (0 == x[1].length ? 0 : parseInt(x[1], 10)) ? -1 : (0 == r[1].length ? 0 : parseInt(r[1], 10)) > (0 == x[1].length ? 0 : parseInt(x[1], 10)) ? 1 : 0) || ((0 == r[2].length) < (0 == x[2].length) ? -1 : (0 == r[2].length) > (0 == x[2].length) ? 1 : 0) || (r[2] < x[2] ? -1 : r[2] > x[2] ? 1 : 0)
    }while(0 == c)
  }
  return c
}
;function ya(a, b) {
  b.unshift(a);
  D.call(this, pa.apply(k, b));
  b.shift();
  this.Lg = a
}
C(ya, D);
ya.prototype.name = "AssertionError";
function za(a, b) {
  f(new ya("Failure" + (a ? ": " + a : ""), Array.prototype.slice.call(arguments, 1)))
}
;var Aa;
Aa = ba(j);
var Ba, Ca, Da, Ea;
function Fa() {
  return t.navigator ? t.navigator.userAgent : k
}
Ea = Da = Ca = Ba = m;
var Ga;
if(Ga = Fa()) {
  var Ha = t.navigator;
  Ba = 0 == Ga.indexOf("Opera");
  Ca = !Ba && -1 != Ga.indexOf("MSIE");
  Da = !Ba && -1 != Ga.indexOf("WebKit");
  Ea = !Ba && !Da && "Gecko" == Ha.product
}
var Ia = Ba, F = Ca, Ja = Ea, H = Da, Ka = t.navigator, La = -1 != (Ka && Ka.platform || "").indexOf("Mac"), Ma;
a: {
  var Na = "", Oa;
  if(Ia && t.opera) {
    var Pa = t.opera.version, Na = "function" == typeof Pa ? Pa() : Pa
  }else {
    if(Ja ? Oa = /rv\:([^\);]+)(\)|;)/ : F ? Oa = /MSIE\s+([^\);]+)(\)|;)/ : H && (Oa = /WebKit\/(\S+)/), Oa) {
      var Qa = Oa.exec(Fa()), Na = Qa ? Qa[1] : ""
    }
  }
  if(F) {
    var Ra, Sa = t.document;
    Ra = Sa ? Sa.documentMode : i;
    if(Ra > parseFloat(Na)) {
      Ma = String(Ra);
      break a
    }
  }
  Ma = Na
}
var Ta = {};
function I(a) {
  return Ta[a] || (Ta[a] = 0 <= xa(Ma, a))
}
var Ua = {};
function Va() {
  return Ua[9] || (Ua[9] = F && !!document.documentMode && 9 <= document.documentMode)
}
;function Wa() {
}
var Xa = 0;
q = Wa.prototype;
q.key = 0;
q.Va = m;
q.cc = m;
q.Ib = function(a, b, c, d, g, e) {
  ja(a) ? this.Dd = j : a && a.handleEvent && ja(a.handleEvent) ? this.Dd = m : f(Error("Invalid listener argument"));
  this.ib = a;
  this.Vd = b;
  this.src = c;
  this.type = d;
  this.capture = !!g;
  this.qc = e;
  this.cc = m;
  this.key = ++Xa;
  this.Va = m
};
q.handleEvent = function(a) {
  return this.Dd ? this.ib.call(this.qc || this.src, a) : this.ib.handleEvent.call(this.ib, a)
};
function Ya(a, b) {
  for(var c in a) {
    b.call(i, a[c], c, a)
  }
}
function Za(a) {
  var b = [], c = 0, d;
  for(d in a) {
    b[c++] = a[d]
  }
  return b
}
function $a(a) {
  var b = [], c = 0, d;
  for(d in a) {
    b[c++] = d
  }
  return b
}
var ab = "constructor hasOwnProperty isPrototypeOf propertyIsEnumerable toLocaleString toString valueOf".split(" ");
function bb(a, b) {
  for(var c, d, g = 1;g < arguments.length;g++) {
    d = arguments[g];
    for(c in d) {
      a[c] = d[c]
    }
    for(var e = 0;e < ab.length;e++) {
      c = ab[e], Object.prototype.hasOwnProperty.call(d, c) && (a[c] = d[c])
    }
  }
}
;!F || Va();
var cb = !F || Va(), db = F && !I("9");
!H || I("528");
Ja && I("1.9b") || F && I("8") || Ia && I("9.5") || H && I("528");
Ja && !I("8") || F && I("9");
var J = Array.prototype, eb = J.indexOf ? function(a, b, c) {
  return J.indexOf.call(a, b, c)
} : function(a, b, c) {
  c = c == k ? 0 : 0 > c ? Math.max(0, a.length + c) : c;
  if(w(a)) {
    return!w(b) || 1 != b.length ? -1 : a.indexOf(b, c)
  }
  for(;c < a.length;c++) {
    if(c in a && a[c] === b) {
      return c
    }
  }
  return-1
}, fb = J.forEach ? function(a, b, c) {
  J.forEach.call(a, b, c)
} : function(a, b, c) {
  for(var d = a.length, g = w(a) ? a.split("") : a, e = 0;e < d;e++) {
    e in g && b.call(c, g[e], e, a)
  }
}, gb = J.filter ? function(a, b, c) {
  return J.filter.call(a, b, c)
} : function(a, b, c) {
  for(var d = a.length, g = [], e = 0, h = w(a) ? a.split("") : a, l = 0;l < d;l++) {
    if(l in h) {
      var n = h[l];
      b.call(c, n, l, a) && (g[e++] = n)
    }
  }
  return g
}, hb = J.map ? function(a, b, c) {
  return J.map.call(a, b, c)
} : function(a, b, c) {
  for(var d = a.length, g = Array(d), e = w(a) ? a.split("") : a, h = 0;h < d;h++) {
    h in e && (g[h] = b.call(c, e[h], h, a))
  }
  return g
}, ib = J.some ? function(a, b, c) {
  return J.some.call(a, b, c)
} : function(a, b, c) {
  for(var d = a.length, g = w(a) ? a.split("") : a, e = 0;e < d;e++) {
    if(e in g && b.call(c, g[e], e, a)) {
      return j
    }
  }
  return m
}, jb = J.every ? function(a, b, c) {
  return J.every.call(a, b, c)
} : function(a, b, c) {
  for(var d = a.length, g = w(a) ? a.split("") : a, e = 0;e < d;e++) {
    if(e in g && !b.call(c, g[e], e, a)) {
      return m
    }
  }
  return j
};
function kb(a, b) {
  var c = eb(a, b);
  0 <= c && J.splice.call(a, c, 1)
}
function lb(a) {
  return J.concat.apply(J, arguments)
}
function mb(a) {
  var b = a.length;
  if(0 < b) {
    for(var c = Array(b), d = 0;d < b;d++) {
      c[d] = a[d]
    }
    return c
  }
  return[]
}
function nb(a, b, c) {
  return 2 >= arguments.length ? J.slice.call(a, b) : J.slice.call(a, b, c)
}
function ob(a, b) {
  return a > b ? 1 : a < b ? -1 : 0
}
;var pb = {If:"click", Nf:"dblclick", ig:"mousedown", mg:"mouseup", lg:"mouseover", kg:"mouseout", jg:"mousemove", yg:"selectstart", dg:"keypress", cg:"keydown", eg:"keyup", Gf:"blur", Xf:"focus", Of:"deactivate", Yf:F ? "focusin" : "DOMFocusIn", Zf:F ? "focusout" : "DOMFocusOut", Hf:"change", xg:"select", zg:"submit", bg:"input", tg:"propertychange", Uf:"dragstart", Pf:"drag", Rf:"dragenter", Tf:"dragover", Sf:"dragleave", Vf:"drop", Qf:"dragend", Dg:"touchstart", Cg:"touchmove", Bg:"touchend", Ag:"touchcancel", 
Ff:"beforeunload", Kf:"contextmenu", Wf:"error", ag:"help", fg:"load", gg:"losecapture", ug:"readystatechange", vg:"resize", wg:"scroll", Fg:"unload", $f:"hashchange", pg:"pagehide", qg:"pageshow", sg:"popstate", Lf:"copy", rg:"paste", Mf:"cut", Cf:"beforecopy", Df:"beforecut", Ef:"beforepaste", og:"online", ng:"offline", hg:"message", Jf:"connect", Eg:H ? "webkitTransitionEnd" : Ia ? "oTransitionEnd" : "transitionend"};
function K() {
  0 != qb && (this.Hg = Error().stack, rb[y(this)] = this)
}
var qb = 0, rb = {};
K.prototype.ja = m;
K.prototype.b = function() {
  if(!this.ja && (this.ja = j, this.d(), 0 != qb)) {
    var a = y(this);
    delete rb[a]
  }
};
K.prototype.d = function() {
  this.Ce && sb.apply(k, this.Ce);
  if(this.Qd) {
    for(;this.Qd.length;) {
      this.Qd.shift()()
    }
  }
};
function sb(a) {
  for(var b = 0, c = arguments.length;b < c;++b) {
    var d = arguments[b];
    ga(d) ? sb.apply(k, d) : d && "function" == typeof d.b && d.b()
  }
}
;function tb(a, b) {
  this.type = a;
  this.currentTarget = this.target = b
}
q = tb.prototype;
q.d = function() {
};
q.b = function() {
};
q.Ga = m;
q.defaultPrevented = m;
q.Ub = j;
q.stopPropagation = function() {
  this.Ga = j
};
q.preventDefault = function() {
  this.defaultPrevented = j;
  this.Ub = m
};
function ub(a) {
  a.stopPropagation()
}
;function vb(a) {
  vb[" "](a);
  return a
}
vb[" "] = ea;
function wb(a, b) {
  a && this.Ib(a, b)
}
C(wb, tb);
q = wb.prototype;
q.target = k;
q.relatedTarget = k;
q.offsetX = 0;
q.offsetY = 0;
q.clientX = 0;
q.clientY = 0;
q.screenX = 0;
q.screenY = 0;
q.button = 0;
q.keyCode = 0;
q.charCode = 0;
q.ctrlKey = m;
q.altKey = m;
q.shiftKey = m;
q.metaKey = m;
q.af = m;
q.bb = k;
q.Ib = function(a, b) {
  var c = this.type = a.type;
  tb.call(this, c);
  this.target = a.target || a.srcElement;
  this.currentTarget = b;
  var d = a.relatedTarget;
  if(d) {
    if(Ja) {
      var g;
      a: {
        try {
          vb(d.nodeName);
          g = j;
          break a
        }catch(e) {
        }
        g = m
      }
      g || (d = k)
    }
  }else {
    "mouseover" == c ? d = a.fromElement : "mouseout" == c && (d = a.toElement)
  }
  this.relatedTarget = d;
  this.offsetX = H || a.offsetX !== i ? a.offsetX : a.layerX;
  this.offsetY = H || a.offsetY !== i ? a.offsetY : a.layerY;
  this.clientX = a.clientX !== i ? a.clientX : a.pageX;
  this.clientY = a.clientY !== i ? a.clientY : a.pageY;
  this.screenX = a.screenX || 0;
  this.screenY = a.screenY || 0;
  this.button = a.button;
  this.keyCode = a.keyCode || 0;
  this.charCode = a.charCode || ("keypress" == c ? a.keyCode : 0);
  this.ctrlKey = a.ctrlKey;
  this.altKey = a.altKey;
  this.shiftKey = a.shiftKey;
  this.metaKey = a.metaKey;
  this.af = La ? a.metaKey : a.ctrlKey;
  this.state = a.state;
  this.bb = a;
  a.defaultPrevented && this.preventDefault();
  delete this.Ga
};
q.stopPropagation = function() {
  wb.n.stopPropagation.call(this);
  this.bb.stopPropagation ? this.bb.stopPropagation() : this.bb.cancelBubble = j
};
q.preventDefault = function() {
  wb.n.preventDefault.call(this);
  var a = this.bb;
  if(a.preventDefault) {
    a.preventDefault()
  }else {
    if(a.returnValue = m, db) {
      try {
        if(a.ctrlKey || 112 <= a.keyCode && 123 >= a.keyCode) {
          a.keyCode = -1
        }
      }catch(b) {
      }
    }
  }
};
q.d = function() {
};
var xb = {}, L = {}, yb = {}, zb = {};
function Ab(a, b, c, d, g) {
  if(b) {
    if(fa(b)) {
      for(var e = 0;e < b.length;e++) {
        Ab(a, b[e], c, d, g)
      }
      return k
    }
    d = !!d;
    var h = L;
    b in h || (h[b] = {c:0, M:0});
    h = h[b];
    d in h || (h[d] = {c:0, M:0}, h.c++);
    var h = h[d], l = y(a), n;
    h.M++;
    if(h[l]) {
      n = h[l];
      for(e = 0;e < n.length;e++) {
        if(h = n[e], h.ib == c && h.qc == g) {
          if(h.Va) {
            break
          }
          return n[e].key
        }
      }
    }else {
      n = h[l] = [], h.c++
    }
    var s = Bb, B = cb ? function(a) {
      return s.call(B.src, B.key, a)
    } : function(a) {
      a = s.call(B.src, B.key, a);
      if(!a) {
        return a
      }
    }, e = B;
    e.src = a;
    h = new Wa;
    h.Ib(c, e, a, b, d, g);
    c = h.key;
    e.key = c;
    n.push(h);
    xb[c] = h;
    yb[l] || (yb[l] = []);
    yb[l].push(h);
    a.addEventListener ? (a == t || !a.fd) && a.addEventListener(b, e, d) : a.attachEvent(b in zb ? zb[b] : zb[b] = "on" + b, e);
    return c
  }
  f(Error("Invalid event type"))
}
function Cb(a, b, c, d, g) {
  if(fa(b)) {
    for(var e = 0;e < b.length;e++) {
      Cb(a, b[e], c, d, g)
    }
    return k
  }
  a = Ab(a, b, c, d, g);
  xb[a].cc = j;
  return a
}
function Db(a, b, c, d, g) {
  if(fa(b)) {
    for(var e = 0;e < b.length;e++) {
      Db(a, b[e], c, d, g)
    }
  }else {
    d = !!d;
    a: {
      e = L;
      if(b in e && (e = e[b], d in e && (e = e[d], a = y(a), e[a]))) {
        a = e[a];
        break a
      }
      a = k
    }
    if(a) {
      for(e = 0;e < a.length;e++) {
        if(a[e].ib == c && a[e].capture == d && a[e].qc == g) {
          Eb(a[e].key);
          break
        }
      }
    }
  }
}
function Eb(a) {
  if(!xb[a]) {
    return m
  }
  var b = xb[a];
  if(b.Va) {
    return m
  }
  var c = b.src, d = b.type, g = b.Vd, e = b.capture;
  c.removeEventListener ? (c == t || !c.fd) && c.removeEventListener(d, g, e) : c.detachEvent && c.detachEvent(d in zb ? zb[d] : zb[d] = "on" + d, g);
  c = y(c);
  yb[c] && (g = yb[c], kb(g, b), 0 == g.length && delete yb[c]);
  b.Va = j;
  if(b = L[d][e][c]) {
    b.Od = j, Fb(d, e, c, b)
  }
  delete xb[a];
  return j
}
function Fb(a, b, c, d) {
  if(!d.Lb && d.Od) {
    for(var g = 0, e = 0;g < d.length;g++) {
      d[g].Va ? d[g].Vd.src = k : (g != e && (d[e] = d[g]), e++)
    }
    d.length = e;
    d.Od = m;
    0 == e && (delete L[a][b][c], L[a][b].c--, 0 == L[a][b].c && (delete L[a][b], L[a].c--), 0 == L[a].c && delete L[a])
  }
}
function Gb(a, b, c, d, g) {
  var e = 1;
  b = y(b);
  if(a[b]) {
    a.M--;
    a = a[b];
    a.Lb ? a.Lb++ : a.Lb = 1;
    try {
      for(var h = a.length, l = 0;l < h;l++) {
        var n = a[l];
        n && !n.Va && (e &= Hb(n, g) !== m)
      }
    }finally {
      a.Lb--, Fb(c, d, b, a)
    }
  }
  return Boolean(e)
}
function Hb(a, b) {
  a.cc && Eb(a.key);
  return a.handleEvent(b)
}
function Bb(a, b) {
  if(!xb[a]) {
    return j
  }
  var c = xb[a], d = c.type, g = L;
  if(!(d in g)) {
    return j
  }
  var g = g[d], e, h;
  if(!cb) {
    e = b || da("window.event");
    var l = j in g, n = m in g;
    if(l) {
      if(0 > e.keyCode || e.returnValue != i) {
        return j
      }
      a: {
        var s = m;
        if(0 == e.keyCode) {
          try {
            e.keyCode = -1;
            break a
          }catch(B) {
            s = j
          }
        }
        if(s || e.returnValue == i) {
          e.returnValue = j
        }
      }
    }
    s = new wb;
    s.Ib(e, this);
    e = j;
    try {
      if(l) {
        for(var r = [], x = s.currentTarget;x;x = x.parentNode) {
          r.push(x)
        }
        h = g[j];
        h.M = h.c;
        for(var G = r.length - 1;!s.Ga && 0 <= G && h.M;G--) {
          s.currentTarget = r[G], e &= Gb(h, r[G], d, j, s)
        }
        if(n) {
          h = g[m];
          h.M = h.c;
          for(G = 0;!s.Ga && G < r.length && h.M;G++) {
            s.currentTarget = r[G], e &= Gb(h, r[G], d, m, s)
          }
        }
      }else {
        e = Hb(c, s)
      }
    }finally {
      r && (r.length = 0)
    }
    return e
  }
  d = new wb(b, this);
  return e = Hb(c, d)
}
var Ib = 0;
function Jb() {
  K.call(this)
}
C(Jb, K);
q = Jb.prototype;
q.fd = j;
q.Ob = k;
q.Jc = aa("Ob");
q.addEventListener = function(a, b, c, d) {
  Ab(this, a, b, c, d)
};
q.removeEventListener = function(a, b, c, d) {
  Db(this, a, b, c, d)
};
q.dispatchEvent = function(a) {
  var b = a.type || a, c = L;
  if(b in c) {
    if(w(a)) {
      a = new tb(a, this)
    }else {
      if(a instanceof tb) {
        a.target = a.target || this
      }else {
        var d = a;
        a = new tb(b, this);
        bb(a, d)
      }
    }
    var d = 1, g, c = c[b], b = j in c, e;
    if(b) {
      g = [];
      for(e = this;e;e = e.Ob) {
        g.push(e)
      }
      e = c[j];
      e.M = e.c;
      for(var h = g.length - 1;!a.Ga && 0 <= h && e.M;h--) {
        a.currentTarget = g[h], d &= Gb(e, g[h], a.type, j, a) && a.Ub != m
      }
    }
    if(m in c) {
      if(e = c[m], e.M = e.c, b) {
        for(h = 0;!a.Ga && h < g.length && e.M;h++) {
          a.currentTarget = g[h], d &= Gb(e, g[h], a.type, m, a) && a.Ub != m
        }
      }else {
        for(g = this;!a.Ga && g && e.M;g = g.Ob) {
          a.currentTarget = g, d &= Gb(e, g, a.type, m, a) && a.Ub != m
        }
      }
    }
    a = Boolean(d)
  }else {
    a = j
  }
  return a
};
q.d = function() {
  Jb.n.d.call(this);
  var a, b = 0, c = a == k;
  a = !!a;
  if(this == k) {
    Ya(yb, function(d) {
      for(var e = d.length - 1;0 <= e;e--) {
        var g = d[e];
        if(c || a == g.capture) {
          Eb(g.key), b++
        }
      }
    })
  }else {
    var d = y(this);
    if(yb[d]) {
      for(var d = yb[d], g = d.length - 1;0 <= g;g--) {
        var e = d[g];
        if(c || a == e.capture) {
          Eb(e.key), b++
        }
      }
    }
  }
  this.Ob = k
};
var Kb = t.window;
Ib++;
Ib++;
/*
 Portions of this code are from MochiKit, received by
 The Closure Authors under the MIT license. All other code is Copyright
 2005-2009 The Closure Authors. All Rights Reserved.
*/
function M(a, b) {
  this.wb = [];
  this.ad = a;
  this.hd = b || k
}
q = M.prototype;
q.$ = m;
q.cb = m;
q.kb = 0;
q.Kc = m;
q.we = m;
q.ub = 0;
q.cancel = function(a) {
  if(this.$) {
    this.mb instanceof M && this.mb.cancel()
  }else {
    if(this.t) {
      var b = this.t;
      delete this.t;
      a ? b.cancel(a) : (b.ub--, 0 >= b.ub && b.cancel())
    }
    this.ad ? this.ad.call(this.hd, this) : this.Kc = j;
    this.$ || this.P(new Lb(this))
  }
};
q.dd = function(a, b) {
  Mb(this, a, b);
  this.kb--;
  0 == this.kb && this.$ && Nb(this)
};
function Mb(a, b, c) {
  a.$ = j;
  a.mb = c;
  a.cb = !b;
  Nb(a)
}
function Ob(a) {
  a.$ && (a.Kc || f(new Pb(a)), a.Kc = m)
}
q.N = function(a) {
  Ob(this);
  Mb(this, j, a)
};
q.P = function(a) {
  Ob(this);
  Mb(this, m, a)
};
q.Ma = function(a, b) {
  return this.Y(a, k, b)
};
q.tb = function(a, b) {
  return this.Y(k, a, b)
};
q.Y = function(a, b, c) {
  this.wb.push([a, b, c]);
  this.$ && Nb(this);
  return this
};
q.bd = function(a) {
  this.Y(a.N, a.P, a);
  return this
};
q.re = function(a) {
  return this.Ma(z(a.$c, a))
};
q.$c = function(a) {
  var b = new M;
  this.bd(b);
  a && (b.t = this, this.ub++);
  return b
};
q.Wc = function(a, b) {
  return this.Y(a, a, b)
};
q.Pe = p("$");
function Qb(a) {
  return ib(a.wb, function(a) {
    return ja(a[1])
  })
}
function Nb(a) {
  a.Tc && (a.$ && Qb(a)) && (t.clearTimeout(a.Tc), delete a.Tc);
  a.t && (a.t.ub--, delete a.t);
  for(var b = a.mb, c = m, d = m;a.wb.length && 0 == a.kb;) {
    var g = a.wb.shift(), e = g[0], h = g[1], g = g[2];
    if(e = a.cb ? h : e) {
      try {
        var l = e.call(g || a.hd, b);
        v(l) && (a.cb = a.cb && (l == b || l instanceof Error), a.mb = b = l);
        b instanceof M && (d = j, a.kb++)
      }catch(n) {
        b = n, a.cb = j, Qb(a) || (c = j)
      }
    }
  }
  a.mb = b;
  d && a.kb && (b.Y(z(a.dd, a, j), z(a.dd, a, m)), b.we = j);
  c && (a.Tc = t.setTimeout(function() {
    f(b)
  }, 0))
}
function Rb(a) {
  var b = new M;
  b.N(a);
  return b
}
function Sb(a) {
  var b = new M;
  b.P(a);
  return b
}
function Pb(a) {
  D.call(this);
  this.Be = a
}
C(Pb, D);
Pb.prototype.message = "Deferred has already fired";
Pb.prototype.name = "AlreadyCalledError";
function Lb(a) {
  D.call(this);
  this.Be = a
}
C(Lb, D);
Lb.prototype.message = "Deferred was cancelled";
Lb.prototype.name = "CancelledError";
function Tb(a) {
  this.z = a;
  this.Ab = [];
  this.ld = [];
  this.ve = z(this.vf, this)
}
Tb.prototype.Qc = k;
Tb.prototype.vf = function() {
  this.Qc = k;
  var a = this.Ab;
  this.Ab = [];
  for(var b = 0;b < a.length;b++) {
    var c = a[b], d = c[0], g = c[1], c = c[2];
    try {
      d.apply(g, c)
    }catch(e) {
      this.z.setTimeout(function() {
        f(e)
      }, 0)
    }
  }
  if(0 == this.Ab.length) {
    a = this.ld;
    this.ld = [];
    for(b = 0;b < a.length;b++) {
      a[b].N(k)
    }
  }
};
var Ub = new Tb(t.window);
function Vb(a) {
  return ja(a) || "object" == typeof a && ja(a.call) && ja(a.apply)
}
;function Wb(a, b) {
  var c = [];
  Xb(new Yb(b), a, c);
  return c.join("")
}
function Yb(a) {
  this.Tb = a
}
function Xb(a, b, c) {
  switch(typeof b) {
    case "string":
      Zb(b, c);
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
      if(fa(b)) {
        var d = b.length;
        c.push("[");
        for(var g = "", e = 0;e < d;e++) {
          c.push(g), g = b[e], Xb(a, a.Tb ? a.Tb.call(b, String(e), g) : g, c), g = ","
        }
        c.push("]");
        break
      }
      c.push("{");
      d = "";
      for(e in b) {
        Object.prototype.hasOwnProperty.call(b, e) && (g = b[e], "function" != typeof g && (c.push(d), Zb(e, c), c.push(":"), Xb(a, a.Tb ? a.Tb.call(b, e, g) : g, c), d = ","))
      }
      c.push("}");
      break;
    case "function":
      break;
    default:
      f(Error("Unknown type: " + typeof b))
  }
}
var $b = {'"':'\\"', "\\":"\\\\", "/":"\\/", "\b":"\\b", "\f":"\\f", "\n":"\\n", "\r":"\\r", "\t":"\\t", "\x0B":"\\u000b"}, ac = /\uffff/.test("\uffff") ? /[\\\"\x00-\x1f\x7f-\uffff]/g : /[\\\"\x00-\x1f\x7f-\xff]/g;
function Zb(a, b) {
  b.push('"', a.replace(ac, function(a) {
    if(a in $b) {
      return $b[a]
    }
    var b = a.charCodeAt(0), g = "\\u";
    16 > b ? g += "000" : 256 > b ? g += "00" : 4096 > b && (g += "0");
    return $b[a] = g + b.toString(16)
  }), '"')
}
;function bc(a, b, c) {
  var d = eb(c, a);
  if(-1 != d) {
    b.push("#CYCLETO:" + (c.length - d) + "#")
  }else {
    c.push(a);
    d = u(a);
    if("boolean" == d || "number" == d || "null" == d || "undefined" == d) {
      b.push(String(a))
    }else {
      if("string" == d) {
        Zb(a, b)
      }else {
        if(Vb(a.v)) {
          a.v(b, c)
        }else {
          if(Vb(a.ne)) {
            b.push("<cw.eq.Wildcard>")
          }else {
            if(a instanceof RegExp) {
              b.push(a.toString())
            }else {
              if("array" == d) {
                d = a.length;
                b.push("[");
                for(var g = "", e = 0;e < d;e++) {
                  b.push(g), bc(a[e], b, c), g = ", "
                }
                b.push("]")
              }else {
                if("object" == d) {
                  if(ha(a) && "function" == typeof a.valueOf) {
                    b.push("new Date(", String(a.valueOf()), ")")
                  }else {
                    for(var d = $a(a).concat(ab), g = {}, h = e = 0;h < d.length;) {
                      var l = d[h++], n = ia(l) ? "o" + y(l) : (typeof l).charAt(0) + l;
                      Object.prototype.hasOwnProperty.call(g, n) || (g[n] = j, d[e++] = l)
                    }
                    d.length = e;
                    b.push("{");
                    g = "";
                    for(h = 0;h < d.length;h++) {
                      e = d[h], Object.prototype.hasOwnProperty.call(a, e) && (l = a[e], b.push(g), Zb(e, b), b.push(": "), bc(l, b, c), g = ", ")
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
function N(a, b, c) {
  c || (c = []);
  bc(a, b, c)
}
function O(a, b) {
  var c = [];
  N(a, c, b);
  return c.join("")
}
;function cc() {
  return Math.floor(2147483648 * Math.random()).toString(36) + Math.abs(Math.floor(2147483648 * Math.random()) ^ oa()).toString(36)
}
function dc(a) {
  return a.substr(0, a.length - 1)
}
var ec = /^(0|[1-9]\d*)$/, fc = /^(0|\-?[1-9]\d*)$/;
function gc(a) {
  var b = hc;
  return ec.test(a) && (a = parseInt(a, 10), a <= b) ? a : k
}
;var hc = Math.pow(2, 53);
function ic(a) {
  if("function" == typeof a.A) {
    a = a.A()
  }else {
    if(ga(a) || w(a)) {
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
function jc(a) {
  if("function" == typeof a.C) {
    return a.C()
  }
  if(w(a)) {
    return a.split("")
  }
  if(ga(a)) {
    for(var b = [], c = a.length, d = 0;d < c;d++) {
      b.push(a[d])
    }
    return b
  }
  return Za(a)
}
function kc(a) {
  if("function" == typeof a.T) {
    return a.T()
  }
  if("function" != typeof a.C) {
    if(ga(a) || w(a)) {
      var b = [];
      a = a.length;
      for(var c = 0;c < a;c++) {
        b.push(c)
      }
      return b
    }
    return $a(a)
  }
}
function mc(a, b, c) {
  if("function" == typeof a.forEach) {
    a.forEach(b, c)
  }else {
    if(ga(a) || w(a)) {
      fb(a, b, c)
    }else {
      for(var d = kc(a), g = jc(a), e = g.length, h = 0;h < e;h++) {
        b.call(c, g[h], d && d[h], a)
      }
    }
  }
}
function nc(a, b) {
  if("function" == typeof a.every) {
    return a.every(b, i)
  }
  if(ga(a) || w(a)) {
    return jb(a, b, i)
  }
  for(var c = kc(a), d = jc(a), g = d.length, e = 0;e < g;e++) {
    if(!b.call(i, d[e], c && c[e], a)) {
      return m
    }
  }
  return j
}
;function P(a, b) {
  this.m = {};
  this.g = [];
  var c = arguments.length;
  if(1 < c) {
    c % 2 && f(Error("Uneven number of arguments"));
    for(var d = 0;d < c;d += 2) {
      this.set(arguments[d], arguments[d + 1])
    }
  }else {
    a && this.bc(a)
  }
}
q = P.prototype;
q.c = 0;
q.Uc = 0;
q.A = p("c");
q.C = function() {
  oc(this);
  for(var a = [], b = 0;b < this.g.length;b++) {
    a.push(this.m[this.g[b]])
  }
  return a
};
q.T = function() {
  oc(this);
  return this.g.concat()
};
q.Z = function(a) {
  return pc(this.m, a)
};
q.fc = function(a) {
  for(var b = 0;b < this.g.length;b++) {
    var c = this.g[b];
    if(pc(this.m, c) && this.m[c] == a) {
      return j
    }
  }
  return m
};
q.K = function(a, b) {
  if(this === a) {
    return j
  }
  if(this.c != a.A()) {
    return m
  }
  var c = b || qc;
  oc(this);
  for(var d, g = 0;d = this.g[g];g++) {
    if(!c(this.get(d), a.get(d))) {
      return m
    }
  }
  return j
};
function qc(a, b) {
  return a === b
}
q.fb = function() {
  return 0 == this.c
};
q.clear = function() {
  this.m = {};
  this.Uc = this.c = this.g.length = 0
};
q.remove = function(a) {
  return pc(this.m, a) ? (delete this.m[a], this.c--, this.Uc++, this.g.length > 2 * this.c && oc(this), j) : m
};
function oc(a) {
  if(a.c != a.g.length) {
    for(var b = 0, c = 0;b < a.g.length;) {
      var d = a.g[b];
      pc(a.m, d) && (a.g[c++] = d);
      b++
    }
    a.g.length = c
  }
  if(a.c != a.g.length) {
    for(var g = {}, c = b = 0;b < a.g.length;) {
      d = a.g[b], pc(g, d) || (a.g[c++] = d, g[d] = 1), b++
    }
    a.g.length = c
  }
}
q.get = function(a, b) {
  return pc(this.m, a) ? this.m[a] : b
};
q.set = function(a, b) {
  pc(this.m, a) || (this.c++, this.g.push(a), this.Uc++);
  this.m[a] = b
};
q.bc = function(a) {
  var b;
  a instanceof P ? (b = a.T(), a = a.C()) : (b = $a(a), a = Za(a));
  for(var c = 0;c < b.length;c++) {
    this.set(b[c], a[c])
  }
};
q.S = function() {
  return new P(this)
};
function rc(a) {
  oc(a);
  for(var b = {}, c = 0;c < a.g.length;c++) {
    var d = a.g[c];
    b[d] = a.m[d]
  }
  return b
}
function pc(a, b) {
  return Object.prototype.hasOwnProperty.call(a, b)
}
;var sc = {ne:ba("<cw.eq.Wildcard>")};
function tc(a) {
  return"boolean" == a || "number" == a || "null" == a || "undefined" == a || "string" == a
}
function uc(a, b, c) {
  var d = u(a), g = u(b);
  if(a == sc || b == sc) {
    return j
  }
  if(a != k && "function" == typeof a.K) {
    return c && c.push("running custom equals function on left object"), a.K(b, c)
  }
  if(b != k && "function" == typeof b.K) {
    return c && c.push("running custom equals function on right object"), b.K(a, c)
  }
  if(tc(d) || tc(g)) {
    a = a === b
  }else {
    if(a instanceof RegExp && b instanceof RegExp) {
      a = a.toString() === b.toString()
    }else {
      if(ha(a) && ha(b)) {
        a = a.valueOf() === b.valueOf()
      }else {
        if("array" == d && "array" == g) {
          a: {
            if(c && c.push("descending into array"), a.length != b.length) {
              c && c.push("array length mismatch: " + a.length + ", " + b.length), a = m
            }else {
              d = 0;
              for(g = a.length;d < g;d++) {
                if(!uc(a[d], b[d], c)) {
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
          if(a.me == Aa && b.me == Aa) {
            a: {
              c && c.push("descending into object");
              for(var e in a) {
                if(!(e in b)) {
                  c && c.push("property " + e + " missing on right object");
                  a = m;
                  break a
                }
                if(!uc(a[e], b[e], c)) {
                  c && c.push("earlier comparisons indicate mismatch at property " + e);
                  a = m;
                  break a
                }
              }
              for(e in b) {
                if(!(e in a)) {
                  c && c.push("property " + e + " missing on left object");
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
;function Q(a, b) {
  this.df = a;
  this.Rb = b
}
Q.prototype.K = function(a, b) {
  return ia(a) && this.constructor == a.constructor && uc(this.Rb, a.Rb, b)
};
Q.prototype.v = function(a, b) {
  a.push("new ", this.df, "(");
  for(var c = "", d = 0;d < this.Rb.length;d++) {
    a.push(c), c = ", ", N(this.Rb[d], a, b)
  }
  a.push(")")
};
var vc, wc;
function xc(a, b) {
  Q.call(this, "Question", [a, b]);
  this.body = a;
  this.ca = b
}
C(xc, Q);
function yc(a, b) {
  Q.call(this, "OkayAnswer", [a, b]);
  this.body = a;
  this.ca = b
}
C(yc, Q);
function zc(a, b) {
  Q.call(this, "KnownErrorAnswer", [a, b]);
  this.body = a;
  this.ca = b
}
C(zc, Q);
function Ac(a, b) {
  Q.call(this, "UnknownErrorAnswer", [a, b]);
  this.body = a;
  this.ca = b
}
C(Ac, Q);
function Bc(a) {
  Q.call(this, "Cancellation", [a]);
  this.ca = a
}
C(Bc, Q);
function Cc(a) {
  Q.call(this, "Notification", [a]);
  this.body = a
}
C(Cc, Q);
function Dc(a) {
  if(a instanceof xc) {
    return"Q"
  }
  if(a instanceof yc) {
    return"K"
  }
  if(a instanceof zc) {
    return"E"
  }
  if(a instanceof Ac) {
    return"U"
  }
  if(a instanceof Bc) {
    return"C"
  }
  if(a instanceof Cc) {
    return"#"
  }
  f(Error("qanTypeToCode bug"))
}
function Ec(a) {
  var b = Dc(a);
  if(a instanceof Bc) {
    return String(a.ca) + b
  }
  w(a.body) || f(Error("qanFrame.body must be a string, was " + O(a.body)));
  return a instanceof Cc ? a.body + b : a.body + "|" + String(a.ca) + b
}
function Fc(a) {
  D.call(this);
  this.message = a
}
C(Fc, D);
function Gc(a) {
  a = gc(a);
  a === k && f(new Fc("bad qid"));
  return a
}
function Hc(a) {
  a || f(new Fc("0-length frame"));
  var b = a.substr(a.length - 1, 1);
  if("#" == b) {
    return new Cc(dc(a))
  }
  if("C" == b) {
    var c = Gc(dc(a));
    return new Bc(c)
  }
  a = a.split("|");
  c = a.splice(a.length - 1, a.length);
  0 < a.length && c.splice(0, 0, a.join("|"));
  a = c[0];
  c = c[1];
  v(c) || f(new Fc("Expected pipe char in frame"));
  c = Gc(dc(c));
  if("Q" == b) {
    return new xc(a, c)
  }
  if("K" == b) {
    return new yc(a, c)
  }
  if("E" == b) {
    return new zc(a, c)
  }
  if("U" == b) {
    return new Ac(a, c)
  }
  f(new Fc("Invalid QAN frame type " + O(b)))
}
function Ic(a) {
  D.call(this);
  this.body = a
}
C(Ic, D);
Ic.prototype.message = "KnownError with arbitrary body";
Ic.prototype.v = function(a, b) {
  a.push("new KnownError(");
  N(this.body, a, b);
  a.push(")")
};
function Jc(a) {
  D.call(this);
  this.body = a
}
C(Jc, D);
Jc.prototype.message = "UnknownError with arbitrary body";
Jc.prototype.v = function(a, b) {
  a.push("new UnknownError(");
  N(this.body, a, b);
  a.push(")")
};
function Kc(a) {
  D.call(this);
  this.message = a
}
C(Kc, D);
function R(a, b, c, d) {
  this.Zc = a;
  this.jb = b;
  this.da = c;
  this.Cb = d;
  this.Qb = 0;
  this.ma = new P;
  this.Ya = new P
}
q = R.prototype;
q.v = function(a) {
  a.push("<QANHelper asked ", String(this.Qb), " questions, waiting for ", String(this.ma.A()), " peer answers and ", String(this.Ya.A()), " local answers>")
};
q.wd = function(a) {
  if(a instanceof yc || a instanceof zc || a instanceof Ac) {
    var b = a.ca, c = this.ma.get(b);
    this.ma.remove(b);
    v(c) ? c !== k && (a instanceof yc ? c.N(a.body) : a instanceof zc ? c.P(new Ic(a.body)) : a instanceof Ac ? c.P(new Jc(a.body)) : f(Error("handleQANFrame bug"))) : this.Cb("Received an answer with invalid qid: " + b)
  }else {
    if(a instanceof Cc) {
      try {
        this.Zc(a.body, m)
      }catch(d) {
        this.jb("Peer's Notification caused uncaught exception", d)
      }
    }else {
      if(a instanceof xc) {
        if(b = a.ca, this.Ya.Z(b)) {
          this.Cb("Received Question with duplicate qid: " + b)
        }else {
          a: {
            a = [a.body, j];
            try {
              c = this.Zc.apply(k, a ? a : [])
            }catch(g) {
              c = Sb(g);
              break a
            }
            c = c instanceof M ? c : c instanceof Error ? Sb(c) : Rb(c)
          }
          this.Ya.set(b, c);
          var e = this;
          c.Y(function(a) {
            var c = b;
            e.Ya.remove(c);
            e.da(new yc(a, c));
            return k
          }, function(a) {
            var c = b;
            e.Ya.remove(c);
            a instanceof Ic ? e.da(new zc(a.body, c)) : a instanceof Lb ? e.da(new Ac("CancelledError", c)) : (e.jb("Peer's Question #" + c + " caused uncaught exception", a), e.da(new Ac("Uncaught exception", c)));
            return k
          });
          c.tb(function(a) {
            this.jb("Bug in QANHelper.sendOkayAnswer_ or sendErrorAnswer_", a);
            return k
          })
        }
      }else {
        a instanceof Bc && (b = a.ca, c = this.Ya.get(b), v(c) && c.cancel())
      }
    }
  }
};
q.qe = function(a) {
  var b = this.Qb + 1;
  this.da(new xc(a, b));
  this.Qb += 1;
  var c = this;
  a = new M(function() {
    c.ma.set(b, k);
    c.da(new Bc(b))
  });
  this.ma.set(b, a);
  return a
};
q.Ze = function(a) {
  this.da(new Cc(a))
};
q.nd = function(a) {
  for(var b = this.ma.T(), c = 0;c < b.length;c++) {
    var d = this.ma.get(b[c]);
    v(d) && (this.ma.set(b[c], k), d.P(new Kc(a)))
  }
};
function Lc() {
  this.Yd = oa()
}
var Mc = new Lc;
Lc.prototype.set = aa("Yd");
Lc.prototype.reset = function() {
  this.set(oa())
};
Lc.prototype.get = p("Yd");
function Nc(a) {
  this.bf = a || "";
  this.mf = Mc
}
Nc.prototype.fe = j;
Nc.prototype.lf = j;
Nc.prototype.kf = j;
Nc.prototype.ge = m;
function Oc(a) {
  return 10 > a ? "0" + a : String(a)
}
function Pc(a, b) {
  var c = (a.ie - b) / 1E3, d = c.toFixed(3), g = 0;
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
function Qc(a) {
  Nc.call(this, a)
}
C(Qc, Nc);
Qc.prototype.ge = j;
function Rc() {
  var a = Math.pow(10, 9);
  return a + Math.random() * (Math.pow(10, 10) - a)
}
;var Sc;
function Tc(a, b) {
  var c;
  c = a.className;
  c = w(c) && c.match(/\S+/g) || [];
  for(var d = nb(arguments, 1), g = c.length + d.length, e = c, h = 0;h < d.length;h++) {
    0 <= eb(e, d[h]) || e.push(d[h])
  }
  a.className = c.join(" ");
  return c.length == g
}
;var Uc = !F || Va(), Vc = !Ja && !F || F && Va() || Ja && I("1.9.1");
F && I("9");
function Wc(a) {
  return a ? new Xc(9 == a.nodeType ? a : a.ownerDocument || a.document) : Sc || (Sc = new Xc)
}
function Yc(a) {
  return w(a) ? document.getElementById(a) : a
}
var Zc = {cellpadding:"cellPadding", cellspacing:"cellSpacing", colspan:"colSpan", frameborder:"frameBorder", height:"height", maxlength:"maxLength", role:"role", rowspan:"rowSpan", type:"type", usemap:"useMap", valign:"vAlign", width:"width"};
function $c(a, b, c) {
  return ad(document, arguments)
}
function ad(a, b) {
  var c = b[0], d = b[1];
  if(!Uc && d && (d.name || d.type)) {
    c = ["<", c];
    d.name && c.push(' name="', E(d.name), '"');
    if(d.type) {
      c.push(' type="', E(d.type), '"');
      var g = {};
      bb(g, d);
      delete g.type;
      d = g
    }
    c.push(">");
    c = c.join("")
  }
  var e = a.createElement(c);
  d && (w(d) ? e.className = d : fa(d) ? Tc.apply(k, [e].concat(d)) : Ya(d, function(a, b) {
    "style" == b ? e.style.cssText = a : "class" == b ? e.className = a : "for" == b ? e.htmlFor = a : b in Zc ? e.setAttribute(Zc[b], a) : 0 == b.lastIndexOf("aria-", 0) || 0 == b.lastIndexOf("data-", 0) ? e.setAttribute(b, a) : e[b] = a
  }));
  2 < b.length && bd(a, e, b, 2);
  return e
}
function bd(a, b, c, d) {
  function g(c) {
    c && b.appendChild(w(c) ? a.createTextNode(c) : c)
  }
  for(;d < c.length;d++) {
    var e = c[d];
    if(ga(e) && !(ia(e) && 0 < e.nodeType)) {
      var h = fb, l;
      a: {
        if((l = e) && "number" == typeof l.length) {
          if(ia(l)) {
            l = "function" == typeof l.item || "string" == typeof l.item;
            break a
          }
          if(ja(l)) {
            l = "function" == typeof l.item;
            break a
          }
        }
        l = m
      }
      h(l ? mb(e) : e, g)
    }else {
      g(e)
    }
  }
}
function Xc(a) {
  this.za = a || t.document || document
}
q = Xc.prototype;
q.rd = Wc;
q.Ba = function(a) {
  return w(a) ? this.za.getElementById(a) : a
};
function cd(a, b) {
  var c;
  c = a.za;
  var d = b && "*" != b ? b.toUpperCase() : "";
  c = c.querySelectorAll && c.querySelector && d ? c.querySelectorAll(d + "") : c.getElementsByTagName(d || "*");
  return c
}
q.ab = function(a, b, c) {
  return ad(this.za, arguments)
};
q.createElement = function(a) {
  return this.za.createElement(a)
};
q.createTextNode = function(a) {
  return this.za.createTextNode(a)
};
q.appendChild = function(a, b) {
  a.appendChild(b)
};
q.append = function(a, b) {
  bd(9 == a.nodeType ? a : a.ownerDocument || a.document, a, arguments, 1)
};
q.qd = function(a) {
  return Vc && a.children != i ? a.children : gb(a.childNodes, function(a) {
    return 1 == a.nodeType
  })
};
q.contains = function(a, b) {
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
};
function dd(a) {
  "number" == typeof a && (a = Math.round(a) + "px");
  return a
}
;function ed(a) {
  this.m = new P;
  a && this.bc(a)
}
function fd(a) {
  var b = typeof a;
  return"object" == b && a || "function" == b ? "o" + y(a) : b.substr(0, 1) + a
}
q = ed.prototype;
q.A = function() {
  return this.m.A()
};
q.add = function(a) {
  this.m.set(fd(a), a)
};
q.bc = function(a) {
  a = jc(a);
  for(var b = a.length, c = 0;c < b;c++) {
    this.add(a[c])
  }
};
q.Fc = function(a) {
  a = jc(a);
  for(var b = a.length, c = 0;c < b;c++) {
    this.remove(a[c])
  }
};
q.remove = function(a) {
  return this.m.remove(fd(a))
};
q.clear = function() {
  this.m.clear()
};
q.fb = function() {
  return this.m.fb()
};
q.contains = function(a) {
  return this.m.Z(fd(a))
};
q.C = function() {
  return this.m.C()
};
q.S = function() {
  return new ed(this)
};
q.K = function(a) {
  var b;
  if(b = this.A() == ic(a)) {
    var c = a;
    a = ic(c);
    this.A() > a ? b = m : (!(c instanceof ed) && 5 < a && (c = new ed(c)), b = nc(this, function(a) {
      if("function" == typeof c.contains) {
        a = c.contains(a)
      }else {
        if("function" == typeof c.fc) {
          a = c.fc(a)
        }else {
          if(ga(c) || w(c)) {
            a = 0 <= eb(c, a)
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
function gd(a) {
  return hd(a || arguments.callee.caller, [])
}
function hd(a, b) {
  var c = [];
  if(0 <= eb(b, a)) {
    c.push("[...circular reference...]")
  }else {
    if(a && 50 > b.length) {
      c.push(id(a) + "(");
      for(var d = a.arguments, g = 0;g < d.length;g++) {
        0 < g && c.push(", ");
        var e;
        e = d[g];
        switch(typeof e) {
          case "object":
            e = e ? "object" : "null";
            break;
          case "string":
            break;
          case "number":
            e = String(e);
            break;
          case "boolean":
            e = e ? "true" : "false";
            break;
          case "function":
            e = (e = id(e)) ? e : "[fn]";
            break;
          default:
            e = typeof e
        }
        40 < e.length && (e = e.substr(0, 40) + "...");
        c.push(e)
      }
      b.push(a);
      c.push(")\n");
      try {
        c.push(hd(a.caller, b))
      }catch(h) {
        c.push("[exception trying to get caller]\n")
      }
    }else {
      a ? c.push("[...long stack...]") : c.push("[end]")
    }
  }
  return c.join("")
}
function id(a) {
  if(jd[a]) {
    return jd[a]
  }
  a = String(a);
  if(!jd[a]) {
    var b = /function ([^\(]+)/.exec(a);
    jd[a] = b ? b[1] : "[Anonymous]"
  }
  return jd[a]
}
var jd = {};
function kd(a, b, c, d, g) {
  this.reset(a, b, c, d, g)
}
kd.prototype.gf = 0;
kd.prototype.nc = k;
kd.prototype.mc = k;
var ld = 0;
kd.prototype.reset = function(a, b, c, d, g) {
  this.gf = "number" == typeof g ? g : ld++;
  this.ie = d || oa();
  this.Ra = a;
  this.Md = b;
  this.Ue = c;
  delete this.nc;
  delete this.mc
};
kd.prototype.Ic = aa("Ra");
function S(a) {
  this.Xe = a
}
S.prototype.t = k;
S.prototype.Ra = k;
S.prototype.ia = k;
S.prototype.Na = k;
function T(a, b) {
  this.name = a;
  this.value = b
}
T.prototype.toString = p("name");
var md = new T("OFF", Infinity), nd = new T("SHOUT", 1200), od = new T("SEVERE", 1E3), pd = new T("WARNING", 900), qd = new T("INFO", 800), rd = new T("CONFIG", 700), sd = new T("FINE", 500), td = new T("FINER", 400), ud = new T("FINEST", 300), vd = new T("ALL", 0);
function U(a) {
  return V.td(a)
}
q = S.prototype;
q.getParent = p("t");
q.qd = function() {
  this.ia || (this.ia = {});
  return this.ia
};
q.Ic = aa("Ra");
function wd(a) {
  if(a.Ra) {
    return a.Ra
  }
  if(a.t) {
    return wd(a.t)
  }
  za("Root logger has no level set.");
  return k
}
q.log = function(a, b, c) {
  if(a.value >= wd(this).value) {
    a = this.Me(a, b, c);
    b = "log:" + a.Md;
    t.console && (t.console.timeStamp ? t.console.timeStamp(b) : t.console.markTimeline && t.console.markTimeline(b));
    t.msWriteProfilerMark && t.msWriteProfilerMark(b);
    for(b = this;b;) {
      c = b;
      var d = a;
      if(c.Na) {
        for(var g = 0, e = i;e = c.Na[g];g++) {
          e(d)
        }
      }
      b = b.getParent()
    }
  }
};
q.Me = function(a, b, c) {
  var d = new kd(a, String(b), this.Xe);
  if(c) {
    d.nc = c;
    var g;
    var e = arguments.callee.caller;
    try {
      var h;
      var l = da("window.location.href");
      if(w(c)) {
        h = {message:c, name:"Unknown error", lineNumber:"Not available", fileName:l, stack:"Not available"}
      }else {
        var n, s, B = m;
        try {
          n = c.lineNumber || c.Te || "Not available"
        }catch(r) {
          n = "Not available", B = j
        }
        try {
          s = c.fileName || c.filename || c.sourceURL || l
        }catch(x) {
          s = "Not available", B = j
        }
        h = B || !c.lineNumber || !c.fileName || !c.stack ? {message:c.message, name:c.name, lineNumber:n, fileName:s, stack:c.stack || "Not available"} : c
      }
      g = "Message: " + E(h.message) + '\nUrl: <a href="view-source:' + h.fileName + '" target="_new">' + h.fileName + "</a>\nLine: " + h.lineNumber + "\n\nBrowser stack:\n" + E(h.stack + "-> ") + "[end]\n\nJS stack traversal:\n" + E(gd(e) + "-> ")
    }catch(G) {
      g = "Exception trying to expose exception! You win, we lose. " + G
    }
    d.mc = g
  }
  return d
};
q.jf = function(a, b) {
  this.log(nd, a, b)
};
q.H = function(a, b) {
  this.log(od, a, b)
};
q.q = function(a, b) {
  this.log(pd, a, b)
};
q.info = function(a, b) {
  this.log(qd, a, b)
};
q.ye = function(a, b) {
  this.log(rd, a, b)
};
q.j = function(a, b) {
  this.log(sd, a, b)
};
q.Ie = function(a, b) {
  this.log(td, a, b)
};
q.s = function(a, b) {
  this.log(ud, a, b)
};
var V = {Mb:{}, nb:k, Ad:function() {
  V.nb || (V.nb = new S(""), V.Mb[""] = V.nb, V.nb.Ic(rd))
}, Ig:function() {
  return V.Mb
}, pc:function() {
  V.Ad();
  return V.nb
}, td:function(a) {
  V.Ad();
  return V.Mb[a] || V.Ae(a)
}, Gg:function(a) {
  return function(b) {
    (a || V.pc()).H("Error: " + b.message + " (" + b.fileName + " @ Line: " + b.Te + ")")
  }
}, Ae:function(a) {
  var b = new S(a), c = a.lastIndexOf("."), d = a.substr(c + 1), c = V.td(a.substr(0, c));
  c.qd()[d] = b;
  b.t = c;
  return V.Mb[a] = b
}};
function yd(a) {
  this.Wd = z(this.oe, this);
  this.pd = new Qc;
  this.Cd = this.pd.fe = m;
  this.h = a;
  this.Ge = this.h.ownerDocument || this.h.document;
  a = Wc(this.h);
  var b = k;
  if(F) {
    a = b = a.za.createStyleSheet(), F ? a.cssText = ".dbg-sev{color:#F00}.dbg-w{color:#C40}.dbg-sh{font-weight:bold;color:#000}.dbg-i{color:#444}.dbg-f{color:#999}.dbg-ev{color:#0A0}.dbg-m{color:#990}.logmsg{border-bottom:1px solid #CCC;padding:2px}.logsep{background-color: #8C8;}.logdiv{border:1px solid #CCC;background-color:#FCFCFC;font:medium monospace}" : a.innerHTML = ".dbg-sev{color:#F00}.dbg-w{color:#C40}.dbg-sh{font-weight:bold;color:#000}.dbg-i{color:#444}.dbg-f{color:#999}.dbg-ev{color:#0A0}.dbg-m{color:#990}.logmsg{border-bottom:1px solid #CCC;padding:2px}.logsep{background-color: #8C8;}.logdiv{border:1px solid #CCC;background-color:#FCFCFC;font:medium monospace}"
  }else {
    var c = cd(a, "head")[0];
    c || (b = cd(a, "body")[0], c = a.ab("head"), b.parentNode.insertBefore(c, b));
    var d = b = a.ab("style");
    F ? d.cssText = ".dbg-sev{color:#F00}.dbg-w{color:#C40}.dbg-sh{font-weight:bold;color:#000}.dbg-i{color:#444}.dbg-f{color:#999}.dbg-ev{color:#0A0}.dbg-m{color:#990}.logmsg{border-bottom:1px solid #CCC;padding:2px}.logsep{background-color: #8C8;}.logdiv{border:1px solid #CCC;background-color:#FCFCFC;font:medium monospace}" : d.innerHTML = ".dbg-sev{color:#F00}.dbg-w{color:#C40}.dbg-sh{font-weight:bold;color:#000}.dbg-i{color:#444}.dbg-f{color:#999}.dbg-ev{color:#0A0}.dbg-m{color:#990}.logmsg{border-bottom:1px solid #CCC;padding:2px}.logsep{background-color: #8C8;}.logdiv{border:1px solid #CCC;background-color:#FCFCFC;font:medium monospace}";
    a.appendChild(c, b)
  }
  this.h.className += " logdiv"
}
yd.prototype.hf = function(a) {
  if(a != this.Cd) {
    var b = V.pc();
    if(a) {
      var c = this.Wd;
      b.Na || (b.Na = []);
      b.Na.push(c)
    }else {
      (b = b.Na) && kb(b, this.Wd), this.Kg = ""
    }
    this.Cd = a
  }
};
yd.prototype.oe = function(a) {
  var b = 100 >= this.h.scrollHeight - this.h.scrollTop - this.h.clientHeight, c = this.Ge.createElement("div");
  c.className = "logmsg";
  var d = this.pd, g;
  switch(a.Ra.value) {
    case nd.value:
      g = "dbg-sh";
      break;
    case od.value:
      g = "dbg-sev";
      break;
    case pd.value:
      g = "dbg-w";
      break;
    case qd.value:
      g = "dbg-i";
      break;
    default:
      g = "dbg-f"
  }
  var e = [];
  e.push(d.bf, " ");
  if(d.fe) {
    var h = new Date(a.ie);
    e.push("[", Oc(h.getFullYear() - 2E3) + Oc(h.getMonth() + 1) + Oc(h.getDate()) + " " + Oc(h.getHours()) + ":" + Oc(h.getMinutes()) + ":" + Oc(h.getSeconds()) + "." + Oc(Math.floor(h.getMilliseconds() / 10)), "] ")
  }
  d.lf && e.push("[", wa(Pc(a, d.mf.get())), "s] ");
  d.kf && e.push("[", E(a.Ue), "] ");
  e.push('<span class="', g, '">', qa(wa(E(a.Md))));
  d.ge && a.nc && e.push("<br>", qa(wa(a.mc || "")));
  e.push("</span><br>");
  c.innerHTML = e.join("");
  this.h.appendChild(c);
  b && (this.h.scrollTop = this.h.scrollHeight)
};
yd.prototype.clear = function() {
  this.h.innerHTML = ""
};
var zd = RegExp("^(?:([^:/?#.]+):)?(?://(?:([^/?#]*)@)?([\\w\\d\\-\\u0100-\\uffff.%]*)(?::([0-9]+))?)?([^?#]+)?(?:\\?([^#]*))?(?:#(.*))?$");
function Ad(a, b) {
  var c = a.match(zd), d = b.match(zd);
  return c[3] == d[3] && c[1] == d[1] && c[4] == d[4]
}
;function Bd(a, b) {
  var c;
  if(a instanceof Bd) {
    this.L = v(b) ? b : a.L, Cd(this, a.ta), c = a.Ka, W(this), this.Ka = c, Dd(this, a.ka), Ed(this, a.Ta), Fd(this, a.na), Gd(this, a.Q.S()), c = a.Aa, W(this), this.Aa = c
  }else {
    if(a && (c = String(a).match(zd))) {
      this.L = !!b;
      Cd(this, c[1] || "", j);
      var d = c[2] || "";
      W(this);
      this.Ka = d ? decodeURIComponent(d) : "";
      Dd(this, c[3] || "", j);
      Ed(this, c[4]);
      Fd(this, c[5] || "", j);
      Gd(this, c[6] || "", j);
      c = c[7] || "";
      W(this);
      this.Aa = c ? decodeURIComponent(c) : ""
    }else {
      this.L = !!b, this.Q = new Hd(k, 0, this.L)
    }
  }
}
q = Bd.prototype;
q.ta = "";
q.Ka = "";
q.ka = "";
q.Ta = k;
q.na = "";
q.Aa = "";
q.Se = m;
q.L = m;
q.toString = function() {
  var a = [], b = this.ta;
  b && a.push(Id(b, Jd), ":");
  if(b = this.ka) {
    a.push("//");
    var c = this.Ka;
    c && a.push(Id(c, Jd), "@");
    a.push(encodeURIComponent(String(b)));
    b = this.Ta;
    b != k && a.push(":", String(b))
  }
  if(b = this.na) {
    this.ka && "/" != b.charAt(0) && a.push("/"), a.push(Id(b, "/" == b.charAt(0) ? Kd : Ld))
  }
  (b = this.Q.toString()) && a.push("?", b);
  (b = this.Aa) && a.push("#", Id(b, Md));
  return a.join("")
};
q.S = function() {
  return new Bd(this)
};
function Cd(a, b, c) {
  W(a);
  a.ta = c ? b ? decodeURIComponent(b) : "" : b;
  a.ta && (a.ta = a.ta.replace(/:$/, ""))
}
function Dd(a, b, c) {
  W(a);
  a.ka = c ? b ? decodeURIComponent(b) : "" : b
}
function Ed(a, b) {
  W(a);
  b ? (b = Number(b), (isNaN(b) || 0 > b) && f(Error("Bad port number " + b)), a.Ta = b) : a.Ta = k
}
function Fd(a, b, c) {
  W(a);
  a.na = c ? b ? decodeURIComponent(b) : "" : b
}
function Gd(a, b, c) {
  W(a);
  b instanceof Hd ? (a.Q = b, a.Q.Hc(a.L)) : (c || (b = Id(b, Nd)), a.Q = new Hd(b, 0, a.L))
}
function W(a) {
  a.Se && f(Error("Tried to modify a read-only Uri"))
}
q.Hc = function(a) {
  this.L = a;
  this.Q && this.Q.Hc(a);
  return this
};
function Od(a) {
  return a instanceof Bd ? a.S() : new Bd(a, i)
}
function Id(a, b) {
  return w(a) ? encodeURI(a).replace(b, Pd) : k
}
function Pd(a) {
  a = a.charCodeAt(0);
  return"%" + (a >> 4 & 15).toString(16) + (a & 15).toString(16)
}
var Jd = /[#\/\?@]/g, Ld = /[\#\?:]/g, Kd = /[\#\?]/g, Nd = /[\#\?@]/g, Md = /#/g;
function Hd(a, b, c) {
  this.F = a || k;
  this.L = !!c
}
function Qd(a) {
  if(!a.l && (a.l = new P, a.c = 0, a.F)) {
    for(var b = a.F.split("&"), c = 0;c < b.length;c++) {
      var d = b[c].indexOf("="), g = k, e = k;
      0 <= d ? (g = b[c].substring(0, d), e = b[c].substring(d + 1)) : g = b[c];
      g = decodeURIComponent(g.replace(/\+/g, " "));
      g = Rd(a, g);
      a.add(g, e ? decodeURIComponent(e.replace(/\+/g, " ")) : "")
    }
  }
}
q = Hd.prototype;
q.l = k;
q.c = k;
q.A = function() {
  Qd(this);
  return this.c
};
q.add = function(a, b) {
  Qd(this);
  this.F = k;
  a = Rd(this, a);
  var c = this.l.get(a);
  c || this.l.set(a, c = []);
  c.push(b);
  this.c++;
  return this
};
q.remove = function(a) {
  Qd(this);
  a = Rd(this, a);
  return this.l.Z(a) ? (this.F = k, this.c -= this.l.get(a).length, this.l.remove(a)) : m
};
q.clear = function() {
  this.l = this.F = k;
  this.c = 0
};
q.fb = function() {
  Qd(this);
  return 0 == this.c
};
q.Z = function(a) {
  Qd(this);
  a = Rd(this, a);
  return this.l.Z(a)
};
q.fc = function(a) {
  var b = this.C();
  return 0 <= eb(b, a)
};
q.T = function() {
  Qd(this);
  for(var a = this.l.C(), b = this.l.T(), c = [], d = 0;d < b.length;d++) {
    for(var g = a[d], e = 0;e < g.length;e++) {
      c.push(b[d])
    }
  }
  return c
};
q.C = function(a) {
  Qd(this);
  var b = [];
  if(a) {
    this.Z(a) && (b = lb(b, this.l.get(Rd(this, a))))
  }else {
    a = this.l.C();
    for(var c = 0;c < a.length;c++) {
      b = lb(b, a[c])
    }
  }
  return b
};
q.set = function(a, b) {
  Qd(this);
  this.F = k;
  a = Rd(this, a);
  this.Z(a) && (this.c -= this.l.get(a).length);
  this.l.set(a, [b]);
  this.c++;
  return this
};
q.get = function(a, b) {
  var c = a ? this.C(a) : [];
  return 0 < c.length ? String(c[0]) : b
};
q.toString = function() {
  if(this.F) {
    return this.F
  }
  if(!this.l) {
    return""
  }
  for(var a = [], b = this.l.T(), c = 0;c < b.length;c++) {
    for(var d = b[c], g = encodeURIComponent(String(d)), d = this.C(d), e = 0;e < d.length;e++) {
      var h = g;
      "" !== d[e] && (h += "=" + encodeURIComponent(String(d[e])));
      a.push(h)
    }
  }
  return this.F = a.join("&")
};
q.S = function() {
  var a = new Hd;
  a.F = this.F;
  this.l && (a.l = this.l.S(), a.c = this.c);
  return a
};
function Rd(a, b) {
  var c = String(b);
  a.L && (c = c.toLowerCase());
  return c
}
q.Hc = function(a) {
  a && !this.L && (Qd(this), this.F = k, mc(this.l, function(a, c) {
    var d = c.toLowerCase();
    c != d && (this.remove(c), this.remove(d), 0 < a.length && (this.F = k, this.l.set(Rd(this, d), mb(a)), this.c += a.length))
  }, this));
  this.L = a
};
function Sd(a) {
  var b = u(a);
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
  f(Error("cannot determine size of object type " + b))
}
;function Td(a, b) {
  this.La = a;
  this.Ha = b
}
Td.prototype.K = function(a) {
  return a instanceof Td && this.La == a.La && this.Ha.join(",") == a.Ha
};
Td.prototype.v = function(a, b) {
  a.push("new SACK(", String(this.La), ", ");
  N(this.Ha, a, b);
  a.push(")")
};
function Ud() {
  this.G = new P
}
Ud.prototype.ya = -1;
Ud.prototype.I = 0;
Ud.prototype.append = function(a) {
  var b = Sd(a);
  this.G.set(this.ya + 1, [a, b]);
  this.ya += 1;
  this.I += b
};
Ud.prototype.v = function(a) {
  a.push("<Queue with ", String(this.G.A()), " item(s), counter=#", String(this.ya), ", size=", String(this.I), ">")
};
function Vd(a) {
  a = a.G.T();
  J.sort.call(a, ob);
  return a
}
function Wd() {
  this.wa = new P
}
Wd.prototype.Ea = -1;
Wd.prototype.I = 0;
function Xd(a) {
  var b = a.wa.T();
  J.sort.call(b, ob);
  return new Td(a.Ea, b)
}
var Yd = {};
function Zd(a, b) {
  switch(u(b)) {
    case "string":
      a.push("<string>", E(b), "</string>");
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
          Object.prototype.hasOwnProperty.call(b, c) && "function" != u(b[c]) && (a.push('<property id="', E(c), '">'), Zd(a, b[c]), a.push("</property>"))
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
  for(var e = g.length, h = 1;h < e;h++) {
    Zd(d, g[h])
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
function ke(a) {
  K.call(this);
  this.Oe = a;
  this.g = []
}
C(ke, K);
var le = [];
ke.prototype.Fc = function() {
  fb(this.g, Eb);
  this.g.length = 0
};
ke.prototype.d = function() {
  ke.n.d.call(this);
  this.Fc()
};
ke.prototype.handleEvent = function() {
  f(Error("EventHandler.handleEvent not implemented"))
};
function me() {
}
me.sd = function() {
  return me.Bd ? me.Bd : me.Bd = new me
};
me.prototype.Ye = 0;
me.sd();
function ne(a) {
  K.call(this);
  this.jc = a || Wc();
  this.ff = oe
}
C(ne, Jb);
ne.prototype.Re = me.sd();
var oe = k;
q = ne.prototype;
q.U = k;
q.Da = m;
q.h = k;
q.ff = k;
q.We = k;
q.t = k;
q.ia = k;
q.xb = k;
q.xf = m;
function pe(a) {
  return a.U || (a.U = ":" + (a.Re.Ye++).toString(36))
}
q.Ba = p("h");
q.getParent = p("t");
q.Jc = function(a) {
  this.t && this.t != a && f(Error("Method not supported"));
  ne.n.Jc.call(this, a)
};
q.rd = p("jc");
q.ab = function() {
  this.h = this.jc.createElement("div")
};
q.zb = function() {
  this.Da = j;
  qe(this, function(a) {
    !a.Da && a.Ba() && a.zb()
  })
};
function re(a) {
  qe(a, function(a) {
    a.Da && re(a)
  });
  a.Gb && a.Gb.Fc();
  a.Da = m
}
q.d = function() {
  ne.n.d.call(this);
  this.Da && re(this);
  this.Gb && (this.Gb.b(), delete this.Gb);
  qe(this, function(a) {
    a.b()
  });
  if(!this.xf && this.h) {
    var a = this.h;
    a && a.parentNode && a.parentNode.removeChild(a)
  }
  this.t = this.We = this.h = this.xb = this.ia = k
};
function qe(a, b) {
  a.ia && fb(a.ia, b, i)
}
q.removeChild = function(a, b) {
  if(a) {
    var c = w(a) ? a : pe(a), d;
    this.xb && c ? (d = this.xb, d = (c in d ? d[c] : i) || k) : d = k;
    a = d;
    c && a && (d = this.xb, c in d && delete d[c], kb(this.ia, a), b && (re(a), a.h && (c = a.h) && c.parentNode && c.parentNode.removeChild(c)), c = a, c == k && f(Error("Unable to set parent component")), c.t = k, ne.n.Jc.call(c, k))
  }
  a || f(Error("Child is not in parent component"));
  return a
};
function se(a, b) {
  ne.call(this, b);
  this.Ke = a;
  this.lc = new ke(this);
  this.Db = new P
}
C(se, ne);
q = se.prototype;
q.a = U("goog.ui.media.FlashObject");
q.zf = "window";
q.Yc = "#000000";
q.pe = "sameDomain";
function te(a, b, c) {
  a.Vc = w(b) ? b : Math.round(b) + "px";
  a.rc = w(c) ? c : Math.round(c) + "px";
  a.Ba() && (b = a.Ba() ? a.Ba().firstChild : k, c = a.Vc, a = a.rc, a == i && f(Error("missing height argument")), b.style.width = dd(c), b.style.height = dd(a))
}
q.zb = function() {
  se.n.zb.call(this);
  var a = this.Ba(), b;
  b = F ? '<object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000" id="%s" name="%s" class="%s"><param name="movie" value="%s"/><param name="quality" value="high"/><param name="FlashVars" value="%s"/><param name="bgcolor" value="%s"/><param name="AllowScriptAccess" value="%s"/><param name="allowFullScreen" value="true"/><param name="SeamlessTabbing" value="false"/>%s</object>' : '<embed quality="high" id="%s" name="%s" class="%s" src="%s" FlashVars="%s" bgcolor="%s" AllowScriptAccess="%s" allowFullScreen="true" SeamlessTabbing="false" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/go/getflashplayer" %s></embed>';
  for(var c = F ? '<param name="wmode" value="%s"/>' : "wmode=%s", c = pa(c, this.zf), d = this.Db.T(), g = this.Db.C(), e = [], h = 0;h < d.length;h++) {
    e.push(encodeURIComponent(String(d[h])) + "=" + encodeURIComponent(String(g[h])))
  }
  b = pa(b, pe(this), pe(this), "goog-ui-media-flash-object", E(this.Ke), E(e.join("&")), this.Yc, this.pe, c);
  a.innerHTML = b;
  this.Vc && this.rc && te(this, this.Vc, this.rc);
  a = this.lc;
  b = this.Ba();
  c = Za(pb);
  fa(c) || (le[0] = c, c = le);
  for(d = 0;d < c.length;d++) {
    g = Ab(b, c[d], ub || a, m, a.Oe || a), a.g.push(g)
  }
};
q.ab = function() {
  this.$d != k && !(0 <= xa(je, this.$d)) && (this.a.q("Required flash version not found:" + this.$d), f(Error("Method not supported")));
  var a = this.rd().createElement("div");
  a.className = "goog-ui-media-flash";
  this.h = a
};
q.d = function() {
  se.n.d.call(this);
  this.Db = k;
  this.lc.b();
  this.lc = k
};
function ue(a) {
  D.call(this, a)
}
C(ue, D);
ue.prototype.name = "cw.loadflash.FlashLoadFailed";
t.__loadFlashObject_callbacks = {};
function ve(a, b) {
  K.call(this);
  this.U = "_" + cc();
  this.Yb = a;
  this.pa = b;
  this.va = a.va
}
C(ve, K);
q = ve.prototype;
q.Fa = j;
q.yb = m;
q.a = U("cw.net.FlashSocket");
q.v = function(a) {
  a.push("<FlashSocket id='");
  a.push(this.U);
  a.push("'>")
};
function we(a, b, c) {
  if("frames" == b) {
    a = a.pa, xe(a.w), ye(a.w, c)
  }else {
    if("stillreceiving" == b) {
      c = a.pa, c.a.s("onstillreceiving"), xe(c.w)
    }else {
      if("connect" == b) {
        a.pa.onconnect()
      }else {
        "close" == b ? (a.Fa = m, a.b()) : "ioerror" == b ? (a.Fa = m, b = a.pa, b.a.q("onioerror: " + O(c)), ze(b.w, m), a.b()) : "securityerror" == b ? (a.Fa = m, b = a.pa, b.a.q("onsecurityerror: " + O(c)), ze(b.w, m), a.b()) : f(Error("bad event: " + b))
      }
    }
  }
}
q.ec = function(a, b) {
  try {
    var c = this.va.CallFunction($d("__FC_connect", this.U, a, b, "<int32/>\n"))
  }catch(d) {
    this.a.H("connect: could not call __FC_connect; Flash probably crashed. Disposing now. Error was: " + d.message);
    this.yb = j;
    this.Fa = m;
    this.b();
    return
  }
  '"OK"' != c && f(Error("__FC_connect failed? ret: " + c))
};
q.sb = function(a) {
  try {
    var b = this.va.CallFunction($d("__FC_writeFrames", this.U, a))
  }catch(c) {
    this.a.H("writeFrames: could not call __FC_writeFrames; Flash probably crashed. Disposing now. Error was: " + c.message);
    this.yb = j;
    this.Fa = m;
    this.b();
    return
  }
  '"OK"' != b && ('"no such instance"' == b ? (this.a.q("Flash no longer knows of " + this.U + "; disposing."), this.b()) : f(Error("__FC_writeFrames failed? ret: " + b)))
};
q.d = function() {
  this.a.info("in disposeInternal, needToCallClose_=" + this.Fa);
  ve.n.d.call(this);
  var a = this.va;
  delete this.va;
  if(this.Fa) {
    try {
      var b = a.CallFunction($d("__FC_close", this.U));
      this.a.info("disposeInternal: __FC_close ret: " + b)
    }catch(c) {
      this.a.H("disposeInternal: could not call __FC_close; Flash probably crashed. Error was: " + c.message), this.yb = j
    }
  }
  if(this.yb) {
    a = this.pa, a.a.q("oncrash"), ze(a.w, j)
  }else {
    this.pa.onclose()
  }
  delete this.pa;
  delete this.Yb.Oa[this.U]
};
function Ae(a, b) {
  K.call(this);
  this.o = a;
  this.va = b;
  this.Oa = {};
  this.dc = "__FST_" + cc();
  t[this.dc] = z(this.Fe, this);
  var c = b.CallFunction($d("__FC_setCallbackFunc", this.dc));
  '"OK"' != c && f(Error("__FC_setCallbackFunc failed? ret: " + c))
}
C(Ae, K);
q = Ae.prototype;
q.a = U("cw.net.FlashSocketTracker");
q.v = function(a, b) {
  a.push("<FlashSocketTracker instances=");
  N(this.Oa, a, b);
  a.push(">")
};
q.hc = function(a) {
  a = new ve(this, a);
  return this.Oa[a.U] = a
};
q.De = function(a, b, c, d) {
  var g = this.Oa[a];
  g ? "frames" == b && d ? (we(g, "ioerror", "FlashConnector hadError while handling data."), g.b()) : we(g, b, c) : this.a.q("Cannot dispatch because we have no instance: " + O([a, b, c, d]))
};
q.Fe = function(a, b, c, d) {
  try {
    var g = this.o;
    g.Ab.push([this.De, this, [a, b, c, d]]);
    g.Qc == k && (g.Qc = g.z.setTimeout(g.ve, 0))
  }catch(e) {
    t.window.setTimeout(function() {
      f(e)
    }, 0)
  }
};
q.d = function() {
  Ae.n.d.call(this);
  for(var a = Za(this.Oa);a.length;) {
    a.pop().b()
  }
  delete this.Oa;
  delete this.va;
  t[this.dc] = i
};
function Be(a) {
  K.call(this);
  this.w = a;
  this.$a = []
}
C(Be, K);
q = Be.prototype;
q.a = U("cw.net.FlashSocketConduit");
q.sb = function(a) {
  this.$a ? (this.a.s("writeFrames: Not connected, can't write " + a.length + " frame(s) yet."), this.$a.push.apply(this.$a, a)) : (this.a.s("writeFrames: Writing " + a.length + " frame(s)."), this.Vb.sb(a))
};
q.ec = function(a, b) {
  this.Vb.ec(a, b)
};
q.onconnect = function() {
  this.a.info("onconnect");
  xe(this.w);
  var a = this.$a;
  this.$a = k;
  a.length && (this.a.s("onconnect: Writing " + a.length + " buffered frame(s)."), this.Vb.sb(a))
};
q.onclose = function() {
  this.a.info("onclose");
  ze(this.w, m)
};
q.d = function() {
  this.a.info("in disposeInternal.");
  Be.n.d.call(this);
  this.Vb.b();
  delete this.w
};
var Ce = [];
function De() {
  var a = new M;
  Ce.push(a);
  return a
}
function Ee(a) {
  var b = Ce;
  Ce = [];
  fb(b, function(b) {
    b.N(a)
  });
  return k
}
function Fe(a) {
  var b = Ce;
  Ce = [];
  fb(b, function(b) {
    b.P(a)
  });
  return k
}
;function X(a) {
  D.call(this, a)
}
C(X, D);
X.prototype.name = "cw.net.InvalidFrame";
function Y() {
  var a = [];
  this.O(a);
  return a.join("")
}
function Ge() {
}
Ge.prototype.K = function(a, b) {
  return!(a instanceof Ge) ? m : uc(He(this), He(a), b)
};
Ge.prototype.v = function(a, b) {
  a.push("<HelloFrame properties=");
  N(He(this), a, b);
  a.push(">")
};
function He(a) {
  return[a.fa, a.Ud, a.yd, a.Zd, a.pb, a.Nc, a.Nd, a.Ld, a.xc, a.Jd, a.ke, a.he, a.sa, a.Jb]
}
Ge.prototype.J = Y;
Ge.prototype.O = function(a) {
  var b = {};
  b.tnum = this.fa;
  b.ver = this.Ud;
  b.format = this.yd;
  b["new"] = this.Zd;
  b.id = this.pb;
  b.ming = this.Nc;
  b.pad = this.Nd;
  b.maxb = this.Ld;
  v(this.xc) && (b.maxt = this.xc);
  b.maxia = this.Jd;
  b.tcpack = this.ke;
  b.eeds = this.he;
  b.sack = this.sa instanceof Td ? dc((new Ie(this.sa)).J()) : this.sa;
  b.seenack = this.Jb instanceof Td ? dc((new Ie(this.Jb)).J()) : this.Jb;
  for(var c in b) {
    b[c] === i && delete b[c]
  }
  a.push(Wb(b), "H")
};
function Je(a) {
  Q.call(this, "StringFrame", [a]);
  this.Pc = a
}
C(Je, Q);
Je.prototype.J = Y;
Je.prototype.O = function(a) {
  a.push(this.Pc, " ")
};
function Ke(a) {
  Q.call(this, "CommentFrame", [a]);
  this.xe = a
}
C(Ke, Q);
Ke.prototype.J = Y;
Ke.prototype.O = function(a) {
  a.push(this.xe, "^")
};
function Le(a) {
  Q.call(this, "SeqNumFrame", [a]);
  this.ee = a
}
C(Le, Q);
Le.prototype.J = Y;
Le.prototype.O = function(a) {
  a.push(String(this.ee), "N")
};
function Oe(a) {
  var b = a.split("|");
  if(2 != b.length) {
    return k
  }
  a: {
    var c = b[1];
    a = hc;
    if(fc.test(c) && (c = parseInt(c, 10), -1 <= c && c <= a)) {
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
      var e = gc(b[d]);
      if(e == k) {
        return k
      }
      c.push(e)
    }
  }
  return new Td(a, c)
}
function Ie(a) {
  Q.call(this, "SackFrame", [a]);
  this.sa = a
}
C(Ie, Q);
Ie.prototype.J = Y;
Ie.prototype.O = function(a) {
  var b = this.sa;
  a.push(b.Ha.join(","), "|", String(b.La));
  a.push("A")
};
function Pe(a) {
  Q.call(this, "StreamStatusFrame", [a]);
  this.Fd = a
}
C(Pe, Q);
Pe.prototype.J = Y;
Pe.prototype.O = function(a) {
  var b = this.Fd;
  a.push(b.Ha.join(","), "|", String(b.La));
  a.push("T")
};
function Qe() {
  Q.call(this, "StreamCreatedFrame", [])
}
C(Qe, Q);
Qe.prototype.J = Y;
Qe.prototype.O = function(a) {
  a.push("C")
};
function Re() {
  Q.call(this, "YouCloseItFrame", [])
}
C(Re, Q);
Re.prototype.J = Y;
Re.prototype.O = function(a) {
  a.push("Y")
};
function Se(a, b) {
  Q.call(this, "ResetFrame", [a, b]);
  this.Xd = a;
  this.Xc = b
}
C(Se, Q);
Se.prototype.J = Y;
Se.prototype.O = function(a) {
  a.push(this.Xd, "|", String(Number(this.Xc)), "!")
};
var Te = {stream_attach_failure:"stream_attach_failure", acked_unsent_strings:"acked_unsent_strings", invalid_frame_type_or_arguments:"invalid_frame_type_or_arguments", frame_corruption:"frame_corruption", rwin_overflow:"rwin_overflow"};
function Ue(a) {
  Q.call(this, "TransportKillFrame", [a]);
  this.reason = a
}
C(Ue, Q);
Ue.prototype.J = Y;
Ue.prototype.O = function(a) {
  a.push(this.reason, "K")
};
function Ve(a) {
  a || f(new X("0-length frame"));
  var b = a.substr(a.length - 1, 1);
  if(" " == b) {
    return new Je(a.substr(0, a.length - 1))
  }
  if("A" == b) {
    return a = Oe(dc(a)), a == k && f(new X("bad sack")), new Ie(a)
  }
  if("N" == b) {
    return a = gc(dc(a)), a == k && f(new X("bad seqNum")), new Le(a)
  }
  if("T" == b) {
    return a = Oe(dc(a)), a == k && f(new X("bad lastSackSeen")), new Pe(a)
  }
  if("Y" == b) {
    return 1 != a.length && f(new X("leading garbage")), new Re
  }
  if("^" == b) {
    return new Ke(a.substr(0, a.length - 1))
  }
  if("C" == b) {
    return 1 != a.length && f(new X("leading garbage")), new Qe
  }
  if("!" == b) {
    return b = a.substr(0, a.length - 3), (255 < b.length || !/^([ -~]*)$/.test(b)) && f(new X("bad reasonString")), a = {"|0":m, "|1":j}[a.substr(a.length - 3, 2)], a == k && f(new X("bad applicationLevel")), new Se(b, a)
  }
  if("K" == b) {
    return a = a.substr(0, a.length - 1), a = Te[a], a == k && f(new X("unknown kill reason: " + a)), new Ue(a)
  }
  f(new X("Invalid frame type " + b))
}
;function We(a, b, c, d) {
  this.contentWindow = a;
  this.Bb = b;
  this.Oc = c;
  this.Le = d
}
We.prototype.v = function(a, b) {
  a.push("<XDRFrame frameId=");
  N(this.Le, a, b);
  a.push(", expandedUrl=");
  N(this.Bb, a, b);
  a.push(", streams=");
  N(this.Oc, a, b);
  a.push(">")
};
function Xe() {
  this.frames = [];
  this.vc = new P
}
Xe.prototype.a = U("cw.net.XDRTracker");
function Ye(a, b) {
  for(var c = Ze, d = 0;d < c.frames.length;d++) {
    var g = c.frames[d], e;
    if(e = 0 == g.Oc.length) {
      e = g.Bb;
      var h = String(a).replace(/([-()\[\]{}+?*.$\^|,:#<!\\])/g, "\\$1").replace(/\x08/g, "\\x08").replace(/%random%/g, "ml" + Array(21).join("\\d"));
      e = RegExp("^" + h + "$").test(e)
    }
    if(e) {
      return c.a.info("Giving " + O(b) + " existing frame " + O(g)), Rb(g)
    }
  }
  d = cc() + cc();
  g = a.replace(/%random%/g, function() {
    return"ml" + String(Math.floor(Rc())) + String(Math.floor(Rc()))
  });
  e = t.location;
  e instanceof Bd || (e = Od(e));
  g instanceof Bd || (g = Od(g));
  var l = e;
  e = g;
  g = l.S();
  (h = !!e.ta) ? Cd(g, e.ta) : h = !!e.Ka;
  if(h) {
    var n = e.Ka;
    W(g);
    g.Ka = n
  }else {
    h = !!e.ka
  }
  h ? Dd(g, e.ka) : h = e.Ta != k;
  n = e.na;
  if(h) {
    Ed(g, e.Ta)
  }else {
    if(h = !!e.na) {
      if("/" != n.charAt(0) && (l.ka && !l.na ? n = "/" + n : (l = g.na.lastIndexOf("/"), -1 != l && (n = g.na.substr(0, l + 1) + n))), ".." == n || "." == n) {
        n = ""
      }else {
        if(!(-1 == n.indexOf("./") && -1 == n.indexOf("/."))) {
          for(var l = 0 == n.lastIndexOf("/", 0), n = n.split("/"), s = [], B = 0;B < n.length;) {
            var r = n[B++];
            "." == r ? l && B == n.length && s.push("") : ".." == r ? ((1 < s.length || 1 == s.length && "" != s[0]) && s.pop(), l && B == n.length && s.push("")) : (s.push(r), l = j)
          }
          n = s.join("/")
        }
      }
    }
  }
  h ? Fd(g, n) : h = "" !== e.Q.toString();
  h ? Gd(g, e.Q.toString() ? decodeURIComponent(e.Q.toString()) : "") : h = !!e.Aa;
  h && (e = e.Aa, W(g), g.Aa = e);
  g = g.toString();
  e = String(t.location).match(zd)[3] || k;
  h = g.match(zd)[3] || k;
  e == h ? (c.a.info("No need to make a real XDRFrame for " + O(b)), c = Rb(new We(t, g, [b], k))) : ((e = Yc("minerva-elements")) || f(Error('makeWindowForUrl_: Page is missing an empty div with id "minerva-elements"; please add one.')), h = new M, c.vc.set(d, [h, g, b]), c.a.info("Creating new XDRFrame " + O(d) + "for " + O(b)), c = $c("iframe", {id:"minerva-xdrframe-" + d, style:"visibility: hidden; height: 0; width: 0; border: 0; margin: 0;", src:g + "xdrframe/?domain=" + document.domain + "&id=" + 
  d}), e.appendChild(c), c = h);
  return c
}
Xe.prototype.Bf = function(a) {
  var b = this.vc.get(a);
  b || f(Error("Unknown frameId " + O(a)));
  this.vc.remove(b);
  var c = b[0];
  a = new We(Yc("minerva-xdrframe-" + a).contentWindow || (Yc("minerva-xdrframe-" + a).contentDocument || Yc("minerva-xdrframe-" + a).contentWindow.document).parentWindow || (Yc("minerva-xdrframe-" + a).contentDocument || Yc("minerva-xdrframe-" + a).contentWindow.document).defaultView, b[1], [b[2]], a);
  this.frames.push(a);
  c.N(a)
};
var Ze = new Xe;
t.__XHRTracker_xdrFrameLoaded = z(Ze.Bf, Ze);
var $e;
$e = m;
var af = Fa();
af && (-1 != af.indexOf("Firefox") || -1 != af.indexOf("Camino") || -1 != af.indexOf("iPhone") || -1 != af.indexOf("iPod") || -1 != af.indexOf("iPad") || -1 != af.indexOf("Android") || -1 != af.indexOf("Chrome") && ($e = j));
var bf = $e;
function cf(a, b, c, d, g, e) {
  M.call(this, g, e);
  this.Id = a;
  this.ic = [];
  this.od = !!b;
  this.Je = !!c;
  this.ze = !!d;
  for(b = 0;b < a.length;b++) {
    a[b].Y(z(this.vd, this, b, j), z(this.vd, this, b, m))
  }
  0 == a.length && !this.od && this.N(this.ic)
}
C(cf, M);
cf.prototype.Pd = 0;
cf.prototype.vd = function(a, b, c) {
  this.Pd++;
  this.ic[a] = [b, c];
  this.$ || (this.od && b ? this.N([a, c]) : this.Je && !b ? this.P(c) : this.Pd == this.Id.length && this.N(this.ic));
  this.ze && !b && (c = k);
  return c
};
cf.prototype.P = function(a) {
  cf.n.P.call(this, a);
  fb(this.Id, function(a) {
    a.cancel()
  })
};
function df(a, b) {
  this.Af = a;
  this.Kd = b
}
df.prototype.uc = 0;
df.prototype.Nb = 0;
df.prototype.oc = m;
function ef(a) {
  var b = [];
  if(a.oc) {
    return[b, 2]
  }
  var c = a.uc, d = a.Af.responseText;
  for(a.uc = d.length;;) {
    c = d.indexOf("\n", c);
    if(-1 == c) {
      break
    }
    var g = d.substr(a.Nb, c - a.Nb), g = g.replace(/\r$/, "");
    if(g.length > a.Kd) {
      return a.oc = j, [b, 2]
    }
    b.push(g);
    a.Nb = c += 1
  }
  return a.uc - a.Nb - 1 > a.Kd ? (a.oc = j, [b, 2]) : [b, 1]
}
;function ff(a, b, c) {
  K.call(this);
  this.w = b;
  this.R = a;
  this.gc = c
}
C(ff, K);
q = ff.prototype;
q.a = U("cw.net.XHRMaster");
q.qa = -1;
q.wc = function(a, b, c) {
  this.gc.__XHRSlave_makeRequest(this.R, a, b, c)
};
q.la = p("qa");
q.zc = function(a, b) {
  1 != b && this.a.H(O(this.R) + " got status != OK: " + b + "; XHRSlave should dispose soon.");
  xe(this.w);
  ye(this.w, a)
};
q.Ac = function(a) {
  this.a.j("ongotheaders_: " + O(a));
  var b = k;
  "Content-Length" in a && (b = gc(a["Content-Length"]));
  a = this.w;
  a.a.j(a.k() + " got Content-Length: " + b);
  a.X == gf && (b == k && (a.a.q("Expected to receive a valid Content-Length, but did not."), b = 5E5), hf(a, 2E3 + 1E3 * (b / 3072)))
};
q.Bc = function(a) {
  1 != a && this.a.j(this.w.k() + "'s XHR's readyState is " + a);
  this.qa = a;
  2 <= this.qa && xe(this.w)
};
q.yc = function() {
  this.w.b()
};
q.d = function() {
  ff.n.d.call(this);
  delete Z.ba[this.R];
  this.gc.__XHRSlave_dispose(this.R);
  delete this.gc
};
function jf() {
  K.call(this);
  this.ba = {}
}
C(jf, K);
q = jf.prototype;
q.a = U("cw.net.XHRMasterTracker");
q.hc = function(a, b) {
  var c = "_" + cc(), d = new ff(c, a, b);
  return this.ba[c] = d
};
q.zc = function(a, b, c) {
  if(Ja) {
    for(var d = [], g = 0, e = b.length;g < e;g++) {
      d[g] = b[g]
    }
    b = d
  }else {
    b = lb(b)
  }
  (d = this.ba[a]) ? d.zc(b, c) : this.a.H("onframes_: no master for " + O(a))
};
q.Ac = function(a, b) {
  var c = this.ba[a];
  c ? c.Ac(b) : this.a.H("ongotheaders_: no master for " + O(a))
};
q.Bc = function(a, b) {
  var c = this.ba[a];
  c ? c.Bc(b) : this.a.H("onreadystatechange_: no master for " + O(a))
};
q.yc = function(a) {
  var b = this.ba[a];
  b ? (delete this.ba[b.R], b.yc()) : this.a.H("oncomplete_: no master for " + O(a))
};
q.d = function() {
  jf.n.d.call(this);
  for(var a = Za(this.ba);a.length;) {
    a.pop().b()
  }
  delete this.ba
};
var Z = new jf;
t.__XHRMaster_onframes = z(Z.zc, Z);
t.__XHRMaster_oncomplete = z(Z.yc, Z);
t.__XHRMaster_ongotheaders = z(Z.Ac, Z);
t.__XHRMaster_onreadystatechange = z(Z.Bc, Z);
function kf(a, b, c) {
  this.V = a;
  this.host = b;
  this.port = c
}
function lf(a, b, c) {
  this.host = a;
  this.port = b;
  this.tf = c
}
function mf(a, b) {
  b || (b = a);
  this.V = a;
  this.ua = b
}
mf.prototype.v = function(a, b) {
  a.push("<HttpEndpoint primaryUrl=");
  N(this.V, a, b);
  a.push(", secondaryUrl=");
  N(this.ua, a, b);
  a.push(">")
};
function nf(a, b, c, d) {
  this.V = a;
  this.Td = b;
  this.ua = c;
  this.ce = d;
  (!(0 == this.V.indexOf("http://") || 0 == this.V.indexOf("https://")) || !(0 == this.ua.indexOf("http://") || 0 == this.ua.indexOf("https://"))) && f(Error("primaryUrl and secondUrl must be absolute URLs with http or https scheme"));
  a = this.Td.location.href;
  Ad(this.V, a) || f(Error("primaryWindow not same origin as primaryUrl: " + a));
  a = this.ce.location.href;
  Ad(this.ua, a) || f(Error("secondaryWindow not same origin as secondaryUrl: " + a))
}
nf.prototype.v = function(a, b) {
  a.push("<ExpandedHttpEndpoint_ primaryUrl=");
  N(this.V, a, b);
  a.push(", secondaryUrl=");
  N(this.ua, a, b);
  a.push(">")
};
var of = new Ke(";)]}");
function pf() {
}
function qf(a) {
  t.setTimeout(function() {
    v(a.message) && a.stack && (a.message += "\n" + a.stack);
    f(a)
  }, 0)
}
function rf(a, b, c) {
  v(b) || (b = j);
  v(c) || (c = j);
  this.Ua = a;
  this.wf = b;
  this.qf = c
}
q = rf.prototype;
q.a = U("cw.net.QANProtocolWrapper");
q.jb = function(a, b) {
  this.a.q(a, b);
  this.qf && qf(b)
};
q.da = function(a) {
  this.Xa.de(Ec(a), this.wf)
};
q.Cb = function(a) {
  this.Xa.reset("QANHelper said: " + a)
};
q.of = function(a) {
  this.Xa = a;
  this.Ec = new R(z(this.Ua.bodyReceived, this.Ua), z(this.jb, this), z(this.da, this), z(this.Cb, this));
  this.Ua.streamStarted.call(this.Ua, this.Xa, this.Ec)
};
q.nf = function(a, b) {
  this.Ec.nd("Stream reset applicationLevel=" + O(b) + ", reason: " + a);
  this.Ua.streamReset.call(this.Ua, a, b)
};
q.pf = function(a) {
  try {
    var b = Hc(a)
  }catch(c) {
    c instanceof Fc || f(c);
    this.Xa.reset("Bad QAN frame.  Did peer send a non-QAN string?");
    return
  }
  this.Ec.wd(b)
};
function sf(a) {
  this.Xa = a
}
sf.prototype.v = function(a, b) {
  a.push("<UserContext for ");
  N(this.Xa, a, b);
  a.push(">")
};
sf.prototype.toString = function() {
  return O(this)
};
function tf(a, b, c, d) {
  Q.call(this, "TransportInfo", [a, b, c, d]);
  this.fa = a;
  this.Jg = b;
  this.Ng = c;
  this.Og = d
}
C(tf, Q);
function $(a, b, c) {
  K.call(this);
  this.r = a;
  this.Mg = b ? b : new pf;
  this.o = c ? c : Ub;
  this.qb = new ed;
  this.pb = cc() + cc();
  this.W = new Ud;
  this.tc = new Wd;
  this.rb = k;
  this.Zb = [];
  this.Ja = new sf(this);
  this.ue = z(this.uf, this);
  H && (this.rb = Cb(t, "load", this.ef, m, this))
}
C($, K);
q = $.prototype;
q.a = U("cw.net.ClientStream");
q.Gd = new Td(-1, []);
q.Hd = new Td(-1, []);
q.maxUndeliveredStrings = 50;
q.maxUndeliveredBytes = 1048576;
q.onstring = k;
q.onstarted = k;
q.Cc = k;
q.Dc = k;
q.onreset = k;
q.ondisconnect = k;
q.Wa = k;
q.Lc = m;
q.Gc = m;
q.B = "1_UNSTARTED";
q.Rc = -1;
q.e = k;
q.p = k;
q.lb = k;
q.Mc = 0;
q.Sd = 0;
q.be = 0;
q.v = function(a, b) {
  a.push("<ClientStream id=");
  N(this.pb, a, b);
  a.push(", state=", String(this.B));
  a.push(", primary=");
  N(this.e, a, b);
  a.push(", secondary=");
  N(this.p, a, b);
  a.push(", resetting=");
  N(this.lb, a, b);
  a.push(">")
};
q.toString = function() {
  return O(this)
};
q.Ne = p("Ja");
q.se = function(a) {
  v(a.streamStarted) || f(Error("Protocol is missing required method streamStarted"));
  v(a.streamReset) || f(Error("Protocol is missing required method streamReset"));
  v(a.stringReceived) || f(Error("Protocol is missing required method stringReceived"));
  this.onstarted = z(a.streamStarted, a);
  this.onreset = z(a.streamReset, a);
  this.onstring = z(a.stringReceived, a);
  this.Cc = v(a.transportCreated) ? z(a.transportCreated, a) : k;
  this.Dc = v(a.transportDestroyed) ? z(a.transportDestroyed, a) : k
};
function uf(a) {
  var b = [-1];
  a.e && b.push(a.e.Sa);
  a.p && b.push(a.p.Sa);
  return Math.max.apply(Math.max, b)
}
function vf(a) {
  if(!("3_STARTED" > a.B)) {
    wf(a);
    var b = 0 != a.W.G.A(), c = Xd(a.tc), d = !c.K(a.Hd) && !(a.e && c.K(a.e.Qa) || a.p && c.K(a.p.Qa)), g = uf(a);
    if((b = b && g < a.W.ya) || d) {
      var e = b && d ? "string(s)+SACK" : b ? "string(s)" : d ? "SACK" : "nothing!?";
      a.e.xa ? (a.a.s("tryToSend_: writing " + e + " to primary"), d && (d = a.e, c != d.Qa && (!d.ea && !d.u.length && xf(d), d.u.push(new Ie(c)), d.Qa = c)), b && yf(a.e, a.W, g + 1), a.e.aa()) : a.p == k ? a.Lc ? (a.a.s("tryToSend_: creating secondary to send " + e), a.p = zf(a, m, j), a.p && (b && yf(a.p, a.W, g + 1), a.p.aa())) : (a.a.s("tryToSend_: not creating a secondary because stream might not exist on server"), a.Gc = j) : a.a.s("tryToSend_: need to send " + e + ", but can't right now")
    }
  }
}
function wf(a) {
  a.Wa != k && (a.o.z.clearTimeout(a.Wa), a.Wa = k)
}
q.uf = function() {
  this.Wa = k;
  vf(this)
};
function Af(a) {
  a.Wa == k && (a.Wa = a.o.z.setTimeout(a.ue, 6))
}
q.ef = function() {
  this.rb = k;
  if(this.e && this.e.Pa()) {
    this.a.info("restartHttpRequests_: aborting primary");
    var a = this.e;
    a.ac = j;
    a.b()
  }
  this.p && this.p.Pa() && (this.a.info("restartHttpRequests_: aborting secondary"), a = this.p, a.ac = j, a.b())
};
q.de = function(a, b) {
  v(b) || (b = j);
  "3_STARTED" < this.B && f(Error("sendString: Can't send in state " + this.B));
  b && (w(a) || f(Error("sendString: not a string: " + O(a))), /^([ -~]*)$/.test(a) || f(Error("sendString: string has illegal chars: " + O(a))));
  this.W.append(a);
  Af(this)
};
function zf(a, b, c) {
  var d;
  a.r instanceof nf ? d = gf : a.r instanceof lf ? d = Bf : f(Error("Don't support endpoint " + O(a.r)));
  a.Rc += 1;
  b = new Cf(a.o, a, a.Rc, d, a.r, b);
  a.a.s("Created: " + b.k());
  if(c) {
    if(a.Cc) {
      c = new tf(b.fa, b.ha, b.ra, b.xa);
      try {
        a.Cc.call(a.Ja, c)
      }catch(g) {
        a.a.q("ontransportcreated raised uncaught exception", g), qf(g)
      }
    }
    if(Df(a)) {
      return k
    }
  }
  a.qb.add(b);
  return b
}
function Ef(a, b, c) {
  var d = new Ff(a.o, a, b, c);
  a.a.s("Created: " + d.k() + ", delay=" + b + ", times=" + c);
  a.qb.add(d);
  return d
}
function Gf(a, b) {
  a.qb.remove(b) || f(Error("transportOffline_: Transport was not removed?"));
  a.a.j("Offline: " + b.k());
  var c = "4_RESETTING" == a.B && b.le;
  if(b instanceof Cf && !c) {
    if(a.Dc) {
      var d = new tf(b.fa, b.ha, b.ra, b.xa);
      try {
        a.Dc.call(a.Ja, d)
      }catch(g) {
        a.a.q("ontransportdestroyed raised uncaught exception", g), qf(g)
      }
    }
    if(Df(a)) {
      return
    }
  }
  a.Mc = b.oa ? a.Mc + b.oa : 0;
  1 <= a.Mc && (a.a.info("transportOffline_: Doing an internal reset because streamPenalty_ reached limit."), Hf(a, "stream penalty reached limit", m), a.b());
  if("3_STARTED" < a.B) {
    c ? (a.a.j("Disposing because resettingTransport_ is done."), a.b()) : a.a.j("Not creating a transport because ClientStream is in state " + a.B)
  }else {
    c = b instanceof Ff;
    if(!c && b.ac) {
      var e = H ? bf ? [0, 1] : [9, 20] : [0, 0], c = e[0], d = e[1];
      a.a.s("getDelayForNextTransport_: " + O({delay:c, times:d}))
    }else {
      if(d = b.cd(), b == a.e ? d ? e = ++a.Sd : c || (e = a.Sd = 0) : d ? e = ++a.be : c || (e = a.be = 0), c || !e) {
        d = c = 0, a.a.s("getDelayForNextTransport_: " + O({count:e, delay:c, times:d}))
      }else {
        var h = 2E3 * Math.min(e, 3), l = Math.floor(4E3 * Math.random()) - 2E3, n = Math.max(0, b.je - b.Sc), d = (c = Math.max(0, h + l - n)) ? 1 : 0;
        a.a.s("getDelayForNextTransport_: " + O({count:e, base:h, variance:l, oldDuration:n, delay:c, times:d}))
      }
    }
    c = [c, d];
    e = c[0];
    c = c[1];
    if(b == a.e) {
      a.e = k;
      if(c) {
        a.e = Ef(a, e, c)
      }else {
        e = uf(a);
        a.e = zf(a, j, j);
        if(!a.e) {
          return
        }
        yf(a.e, a.W, e + 1)
      }
      a.e.aa()
    }else {
      b == a.p && (a.p = k, c ? (a.p = Ef(a, e, c), a.p.aa()) : vf(a))
    }
  }
}
function Hf(a, b, c) {
  if(a.onreset) {
    try {
      a.onreset.call(a.Ja, b, c)
    }catch(d) {
      a.a.q("onreset raised uncaught exception", d), qf(d)
    }
  }
}
q.reset = function(a) {
  "3_STARTED" < this.B && f(Error("reset: Can't send reset in state " + this.B));
  wf(this);
  0 != this.W.G.A() && this.a.q("reset: strings in send queue will never be sent: " + O(this.W));
  this.B = "4_RESETTING";
  this.e && this.e.xa ? (this.a.info("reset: Sending ResetFrame over existing primary."), If(this.e, a), this.e.aa()) : (this.e && (this.a.j("reset: Disposing primary before sending ResetFrame."), this.e.b()), this.p && (this.a.j("reset: Disposing secondary before sending ResetFrame."), this.p.b()), this.a.info("reset: Creating resettingTransport_ for sending ResetFrame."), this.lb = zf(this, m, m), If(this.lb, a), this.lb.aa());
  Hf(this, a, j)
};
function Df(a) {
  return"4_RESETTING" == a.B || a.ja
}
q.kd = function(a) {
  this.a.H("Failed to start " + O(this) + "; error was " + O(a.message));
  this.b();
  return k
};
q.start = function() {
  this.onmessage && f(Error("ClientStream.start: Hey, you! It's `onstring`, not `onmessage`! Refusing to start."));
  "1_UNSTARTED" != this.B && f(Error("ClientStream.start: " + O(this) + " already started"));
  if(this.onstarted) {
    this.onstarted(this)
  }
  this.B = "2_WAITING_RESOURCES";
  if(this.r instanceof mf) {
    var a = Ye(this.r.V, this), b = Ye(this.r.ua, this), a = new cf([a, b], m, j);
    a.Ma(function(a) {
      return hb(a, function(a) {
        return a[1]
      })
    });
    a.Ma(z(this.He, this));
    a.tb(z(this.kd, this))
  }else {
    if(this.r instanceof kf) {
      if(wc) {
        this.md()
      }else {
        a = this.o;
        b = this.r.V;
        if(Ce.length) {
          a = De()
        }else {
          b = new se(b + "FlashConnector.swf?cb=4bdfc178fc0e508c0cd5efc3fdb09920");
          b.Yc = "#777777";
          te(b, 300, 30);
          var c = Yc("minerva-elements");
          c || f(Error('loadFlashConnector_: Page is missing an empty div with id "minerva-elements"; please add one.'));
          var d = Yc("minerva-elements-FlashConnectorSwf");
          d || (d = $c("div", {id:"minerva-elements-FlashConnectorSwf"}), c.appendChild(d));
          var g = a.z, e;
          var a = d, h, l = function() {
            h && delete t.__loadFlashObject_callbacks[h]
          };
          if(Ja && !I("1.8.1.20")) {
            e = Sb(new ue("Flash corrupts Error hierarchy in Firefox 2.0.0.0; disabled for all < 2.0.0.20"))
          }else {
            if(0 <= xa(je, "9")) {
              var n;
              h = "_" + cc();
              var s = new M(l);
              t.__loadFlashObject_callbacks[h] = function() {
                g.setTimeout(function() {
                  l();
                  s.N(Yc(n))
                }, 0)
              };
              b.Db.set("onloadcallback", '__loadFlashObject_callbacks["' + h + '"]()');
              n = pe(b);
              b.Da && f(Error("Component already rendered"));
              b.h || b.ab();
              a ? a.insertBefore(b.h, k) : b.jc.za.body.appendChild(b.h);
              (!b.t || b.t.Da) && b.zb();
              e = s
            }else {
              e = Sb(new ue("Need Flash Player 9+; had " + (je ? je : "none")))
            }
          }
          var B = g.setTimeout(function() {
            e.cancel()
          }, 8E3);
          e.Wc(function(a) {
            g.clearTimeout(B);
            return a
          });
          vc = e;
          a = De();
          vc.Y(Ee, Fe)
        }
        var r = this;
        a.Ma(function(a) {
          wc || (wc = new Ae(r.o, a));
          return k
        });
        a.Ma(z(this.md, this));
        a.tb(z(this.kd, this))
      }
    }else {
      Jf(this)
    }
  }
};
q.He = function(a) {
  var b = a[0].contentWindow, c = a[1].contentWindow, d = a[0].Bb, g = a[1].Bb;
  this.Zb.push(a[0]);
  this.Zb.push(a[1]);
  this.r = new nf(d, b, g, c);
  Jf(this)
};
q.md = function() {
  this.r = new lf(this.r.host, this.r.port, wc);
  Jf(this)
};
function Jf(a) {
  a.B = "3_STARTED";
  a.e = zf(a, j, j);
  a.e && (yf(a.e, a.W, k), a.e.aa())
}
q.d = function() {
  this.a.info(O(this) + " in disposeInternal.");
  wf(this);
  this.B = "5_DISCONNECTED";
  for(var a = this.qb.C(), b = 0;b < a.length;b++) {
    a[b].b()
  }
  for(a = 0;a < this.Zb.length;a++) {
    kb(this.Zb[a].Oc, this)
  }
  H && this.rb && (Eb(this.rb), this.rb = k);
  this.ondisconnect && this.ondisconnect.call(this.Ja);
  delete this.qb;
  delete this.e;
  delete this.p;
  delete this.lb;
  delete this.Ja;
  $.n.d.call(this)
};
var gf = 1, Bf = 3;
function Cf(a, b, c, d, g, e) {
  K.call(this);
  this.o = a;
  this.D = b;
  this.fa = c;
  this.X = d;
  this.r = g;
  this.u = [];
  this.ha = e;
  this.xa = !this.Pa();
  this.ra = this.X != gf;
  this.te = z(this.rf, this)
}
C(Cf, K);
q = Cf.prototype;
q.a = U("cw.net.ClientTransport");
q.i = k;
q.Sc = k;
q.je = k;
q.Sb = k;
q.ea = m;
q.Wb = m;
q.Qa = k;
q.Eb = 0;
q.Sa = -1;
q.Pb = -1;
q.le = m;
q.ac = m;
q.oa = 0;
q.eb = m;
q.v = function(a) {
  a.push("<ClientTransport #", String(this.fa), ", becomePrimary=", String(this.ha), ">")
};
q.k = function() {
  return(this.ha ? "Prim. T#" : "Sec. T#") + this.fa
};
q.cd = function() {
  return!(!this.eb && this.Eb)
};
q.Pa = function() {
  return this.X == gf || 2 == this.X
};
function Kf(a, b) {
  J.sort.call(b, function(a, b) {
    return a[0] > b[0] ? 1 : a[0] < b[0] ? -1 : 0
  } || ob);
  a: {
    var c = a.D, d = !a.ra, g, e = c.tc;
    g = c.maxUndeliveredStrings;
    for(var h = c.maxUndeliveredBytes, l = [], n = m, s = 0, B = b.length;s < B;s++) {
      var r = b[s], x = r[0], r = r[1];
      if(x == e.Ea + 1) {
        e.Ea += 1;
        for(l.push(r);;) {
          x = e.Ea + 1;
          r = e.wa.get(x, Yd);
          if(r === Yd) {
            break
          }
          l.push(r[0]);
          e.wa.remove(x);
          e.I -= r[1];
          e.Ea = x
        }
      }else {
        if(!(x <= e.Ea)) {
          if(g != k && e.wa.A() >= g) {
            n = j;
            break
          }
          var G = Sd(r);
          if(h != k && e.I + G > h) {
            n = j;
            break
          }
          e.wa.set(x, [r, G]);
          e.I += G
        }
      }
    }
    e.wa.fb() && e.wa.clear();
    g = [l, n];
    e = g[0];
    g = g[1];
    if(e) {
      for(h = 0;h < e.length;h++) {
        l = e[h];
        if(c.onstring) {
          try {
            c.onstring.call(c.Ja, l)
          }catch(lc) {
            c.a.q("onstring raised uncaught exception", lc), qf(lc)
          }
        }
        if(Df(c)) {
          break a
        }
      }
    }
    d || Af(c);
    !Df(c) && g && (a.a.H(a.k() + "'s peer caused rwin overflow."), a.b())
  }
}
function Lf(a, b, c) {
  try {
    var d = Ve(b);
    a.Eb += 1;
    a.a.j(a.k() + " RECV " + O(d));
    var g;
    1 == a.Eb && !d.K(of) && a.Pa() ? (a.a.q(a.k() + " is closing soon because got bad preamble: " + O(d)), g = j) : g = m;
    if(g) {
      return j
    }
    if(d instanceof Je) {
      if(!/^([ -~]*)$/.test(d.Pc)) {
        return a.eb = j
      }
      a.Pb += 1;
      c.push([a.Pb, d.Pc])
    }else {
      if(d instanceof Ie) {
        var e = a.D, h = d.sa;
        e.Gd = h;
        var l = e.W, n = h.La;
        c = m;
        n > l.ya && (c = j);
        for(var s = Vd(l).concat(), d = 0;d < s.length;d++) {
          var B = s[d];
          if(B > n) {
            break
          }
          var r = l.G.get(B)[1];
          l.G.remove(B);
          l.I -= r
        }
        for(d = 0;d < h.Ha.length;d++) {
          var x = h.Ha[d];
          x > l.ya && (c = j);
          l.G.Z(x) && (r = l.G.get(x)[1], l.G.remove(x), l.I -= r)
        }
        l.G.fb() && l.G.clear();
        if(c) {
          return a.a.q(a.k() + " is closing soon because got bad SackFrame"), a.eb = j
        }
      }else {
        if(d instanceof Le) {
          a.Pb = d.ee - 1
        }else {
          if(d instanceof Pe) {
            a.D.Hd = d.Fd
          }else {
            if(d instanceof Re) {
              return a.a.s(a.k() + " is closing soon because got YouCloseItFrame"), j
            }
            if(d instanceof Ue) {
              return a.eb = j, "stream_attach_failure" == d.reason ? a.oa += 1 : "acked_unsent_strings" == d.reason && (a.oa += 0.5), a.a.s(a.k() + " is closing soon because got " + O(d)), j
            }
            if(!(d instanceof Ke)) {
              if(d instanceof Qe) {
                var G = a.D, lc = !a.ra;
                G.a.s("Stream is now confirmed to exist at server.");
                G.Lc = j;
                G.Gc && !lc && (G.Gc = m, vf(G))
              }else {
                if(c.length) {
                  Kf(a, c);
                  if(!fa(c)) {
                    for(var xd = c.length - 1;0 <= xd;xd--) {
                      delete c[xd]
                    }
                  }
                  c.length = 0
                }
                if(d instanceof Se) {
                  var Me = a.D;
                  Hf(Me, d.Xd, d.Xc);
                  Me.b();
                  return j
                }
                f(Error(a.k() + " had unexpected state in framesReceived_."))
              }
            }
          }
        }
      }
    }
  }catch(Ne) {
    return Ne instanceof X || f(Ne), a.a.q(a.k() + " is closing soon because got InvalidFrame: " + O(b)), a.eb = j
  }
  return m
}
function ye(a, b) {
  a.Wb = j;
  try {
    for(var c = m, d = [], g = 0, e = b.length;g < e;g++) {
      if(a.ja) {
        a.a.info(a.k() + " returning from loop because we're disposed.");
        return
      }
      if(c = Lf(a, b[g], d)) {
        break
      }
    }
    d.length && Kf(a, d);
    a.Wb = m;
    a.u.length && a.aa();
    c && (a.a.s(a.k() + " closeSoon is true.  Frames were: " + O(b)), a.b())
  }finally {
    a.Wb = m
  }
}
q.rf = function() {
  this.a.q(this.k() + " timed out due to lack of connection or no data being received.");
  this.b()
};
function Mf(a) {
  a.Sb != k && (a.o.z.clearTimeout(a.Sb), a.Sb = k)
}
function hf(a, b) {
  Mf(a);
  b = Math.round(b);
  a.Sb = a.o.z.setTimeout(a.te, b);
  a.a.j(a.k() + "'s receive timeout set to " + b + " ms.")
}
function xe(a) {
  a.X != gf && (a.X == Bf || 2 == a.X ? hf(a, 13500) : f(Error("peerStillAlive_: Don't know what to do for this transportType: " + a.X)))
}
function xf(a) {
  var b = new Ge;
  b.fa = a.fa;
  b.Ud = 2;
  b.yd = 2;
  a.D.Lc || (b.Zd = j);
  b.pb = a.D.pb;
  b.Nc = a.ra;
  b.Nc && (b.Nd = 4096);
  b.Ld = 3E5;
  b.Jd = a.ra ? Math.floor(10) : 0;
  b.ke = m;
  a.ha && (b.he = k, b.xc = Math.floor((a.ra ? 358E4 : 25E3) / 1E3));
  b.sa = Xd(a.D.tc);
  b.Jb = a.D.Gd;
  a.u.push(b);
  a.Qa = b.sa
}
function ze(a, b) {
  b && (a.oa += 0.5);
  a.b()
}
q.aa = function() {
  this.ea && !this.xa && f(Error("flush_: Can't flush more than once to this transport."));
  if(this.Wb) {
    this.a.s(this.k() + " flush_: Returning because spinning right now.")
  }else {
    var a = this.ea;
    this.ea = j;
    !a && !this.u.length && xf(this);
    for(a = 0;a < this.u.length;a++) {
      this.a.j(this.k() + " SEND " + O(this.u[a]))
    }
    if(this.Pa()) {
      for(var a = [], b = 0, c = this.u.length;b < c;b++) {
        this.u[b].O(a), a.push("\n")
      }
      this.u = [];
      a = a.join("");
      b = this.ha ? this.r.V : this.r.ua;
      this.i = Z.hc(this, this.ha ? this.r.Td : this.r.ce);
      this.Sc = this.o.z === Kb ? oa() : this.o.z.getTime();
      this.i.wc(b, "POST", a);
      hf(this, 3E3 * (1.5 + (0 == b.indexOf("https://") ? 3 : 1)) + 4E3 + (this.ra ? 0 : this.ha ? 25E3 : 0))
    }else {
      if(this.X == Bf) {
        a = [];
        b = 0;
        for(c = this.u.length;b < c;b++) {
          a.push(this.u[b].J())
        }
        this.u = [];
        this.i ? this.i.sb(a) : (b = this.r, this.i = new Be(this), c = b.tf.hc(this.i), this.i.Vb = c, this.Sc = this.o.z === Kb ? oa() : this.o.z.getTime(), this.i.ec(b.host, b.port), this.i.ja || (this.i.sb(a), this.i.ja || hf(this, 8E3)))
      }else {
        f(Error("flush_: Don't know what to do for this transportType: " + this.X))
      }
    }
  }
};
function yf(a, b, c) {
  !a.ea && !a.u.length && xf(a);
  var d = Math.max(c, a.Sa + 1), g = Vd(b);
  c = [];
  for(var e = 0;e < g.length;e++) {
    var h = g[e];
    (d == k || h >= d) && c.push([h, b.G.get(h)[0]])
  }
  b = 0;
  for(d = c.length;b < d;b++) {
    e = c[b], g = e[0], e = e[1], (-1 == a.Sa || a.Sa + 1 != g) && a.u.push(new Le(g)), a.u.push(new Je(e)), a.Sa = g
  }
}
q.d = function() {
  this.a.info(this.k() + " in disposeInternal.");
  Cf.n.d.call(this);
  this.je = this.o.z === Kb ? oa() : this.o.z.getTime();
  this.u = [];
  Mf(this);
  this.i && this.i.b();
  var a = this.D;
  this.D = k;
  Gf(a, this)
};
function If(a, b) {
  !a.ea && !a.u.length && xf(a);
  a.u.push(new Se(b, j));
  a.le = j
}
function Ff(a, b, c, d) {
  K.call(this);
  this.o = a;
  this.D = b;
  this.jd = c;
  this.ed = d
}
C(Ff, K);
q = Ff.prototype;
q.ea = m;
q.xa = m;
q.Fb = k;
q.Qa = k;
q.a = U("cw.net.DoNothingTransport");
function Nf(a) {
  a.Fb = a.o.z.setTimeout(function() {
    a.Fb = k;
    a.ed--;
    a.ed ? Nf(a) : a.b()
  }, a.jd)
}
q.aa = function() {
  this.ea && !this.xa && f(Error("flush_: Can't flush more than once to DoNothingTransport."));
  this.ea = j;
  Nf(this)
};
q.v = function(a) {
  a.push("<DoNothingTransport delay=", String(this.jd), ">")
};
q.Pa = ba(m);
q.k = ba("Wast. T");
q.cd = ba(m);
q.d = function() {
  this.a.info(this.k() + " in disposeInternal.");
  Ff.n.d.call(this);
  this.Fb != k && this.o.z.clearTimeout(this.Fb);
  var a = this.D;
  this.D = k;
  Gf(a, this)
};
function Of() {
}
Of.prototype.vb = k;
var Pf;
function Qf() {
}
C(Qf, Of);
function Rf(a) {
  return(a = Sf(a)) ? new ActiveXObject(a) : new XMLHttpRequest
}
function Tf(a) {
  var b = {};
  Sf(a) && (b[0] = j, b[1] = j);
  return b
}
function Sf(a) {
  if(!a.zd && "undefined" == typeof XMLHttpRequest && "undefined" != typeof ActiveXObject) {
    for(var b = ["MSXML2.XMLHTTP.6.0", "MSXML2.XMLHTTP.3.0", "MSXML2.XMLHTTP", "Microsoft.XMLHTTP"], c = 0;c < b.length;c++) {
      var d = b[c];
      try {
        return new ActiveXObject(d), a.zd = d
      }catch(g) {
      }
    }
    f(Error("Could not create ActiveXObject. ActiveX might be disabled, or MSXML might not be installed"))
  }
  return a.zd
}
Pf = new Qf;
function Uf(a) {
  K.call(this);
  this.headers = new P;
  this.Za = a || k
}
C(Uf, Jb);
Uf.prototype.a = U("goog.net.XhrIo");
var Vf = /^https?$/i;
q = Uf.prototype;
q.ga = m;
q.f = k;
q.$b = k;
q.Kb = "";
q.Ed = "";
q.gb = 0;
q.hb = "";
q.kc = m;
q.Hb = m;
q.sc = m;
q.Ca = m;
q.Xb = 0;
q.Ia = k;
q.ae = "";
q.yf = m;
q.send = function(a, b, c, d) {
  this.f && f(Error("[goog.net.XhrIo] Object is active with another request=" + this.Kb + "; newUri=" + a));
  b = b ? b.toUpperCase() : "GET";
  this.Kb = a;
  this.hb = "";
  this.gb = 0;
  this.Ed = b;
  this.kc = m;
  this.ga = j;
  this.f = this.Za ? Rf(this.Za) : Rf(Pf);
  this.$b = this.Za ? this.Za.vb || (this.Za.vb = Tf(this.Za)) : Pf.vb || (Pf.vb = Tf(Pf));
  this.f.onreadystatechange = z(this.Rd, this);
  try {
    this.a.j(Wf(this, "Opening Xhr")), this.sc = j, this.f.open(b, a, j), this.sc = m
  }catch(g) {
    this.a.j(Wf(this, "Error opening Xhr: " + g.message));
    Xf(this, g);
    return
  }
  a = c || "";
  var e = this.headers.S();
  d && mc(d, function(a, b) {
    e.set(b, a)
  });
  d = t.FormData && a instanceof t.FormData;
  "POST" == b && (!e.Z("Content-Type") && !d) && e.set("Content-Type", "application/x-www-form-urlencoded;charset=utf-8");
  mc(e, function(a, b) {
    this.f.setRequestHeader(b, a)
  }, this);
  this.ae && (this.f.responseType = this.ae);
  "withCredentials" in this.f && (this.f.withCredentials = this.yf);
  try {
    this.Ia && (Kb.clearTimeout(this.Ia), this.Ia = k), 0 < this.Xb && (this.a.j(Wf(this, "Will abort after " + this.Xb + "ms if incomplete")), this.Ia = Kb.setTimeout(z(this.sf, this), this.Xb)), this.a.j(Wf(this, "Sending request")), this.Hb = j, this.f.send(a), this.Hb = m
  }catch(h) {
    this.a.j(Wf(this, "Send error: " + h.message)), Xf(this, h)
  }
};
q.sf = function() {
  "undefined" != typeof ca && this.f && (this.hb = "Timed out after " + this.Xb + "ms, aborting", this.gb = 8, this.a.j(Wf(this, this.hb)), this.dispatchEvent("timeout"), this.abort(8))
};
function Xf(a, b) {
  a.ga = m;
  a.f && (a.Ca = j, a.f.abort(), a.Ca = m);
  a.hb = b;
  a.gb = 5;
  Yf(a);
  Zf(a)
}
function Yf(a) {
  a.kc || (a.kc = j, a.dispatchEvent("complete"), a.dispatchEvent("error"))
}
q.abort = function(a) {
  this.f && this.ga && (this.a.j(Wf(this, "Aborting")), this.ga = m, this.Ca = j, this.f.abort(), this.Ca = m, this.gb = a || 7, this.dispatchEvent("complete"), this.dispatchEvent("abort"), Zf(this))
};
q.d = function() {
  this.f && (this.ga && (this.ga = m, this.Ca = j, this.f.abort(), this.Ca = m), Zf(this, j));
  Uf.n.d.call(this)
};
q.Rd = function() {
  !this.sc && !this.Hb && !this.Ca ? this.$e() : $f(this)
};
q.$e = function() {
  $f(this)
};
function $f(a) {
  if(a.ga && "undefined" != typeof ca) {
    if(a.$b[1] && 4 == a.la() && 2 == ag(a)) {
      a.a.j(Wf(a, "Local request error detected and ignored"))
    }else {
      if(a.Hb && 4 == a.la()) {
        Kb.setTimeout(z(a.Rd, a), 0)
      }else {
        if(a.dispatchEvent("readystatechange"), 4 == a.la()) {
          a.a.j(Wf(a, "Request complete"));
          a.ga = m;
          try {
            var b = ag(a), c, d;
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
                  d = j;
                  break a;
                default:
                  d = m
              }
            }
            if(!(c = d)) {
              var g;
              if(g = 0 === b) {
                var e = String(a.Kb).match(zd)[1] || k;
                if(!e && self.location) {
                  var h = self.location.protocol, e = h.substr(0, h.length - 1)
                }
                g = !Vf.test(e ? e.toLowerCase() : "")
              }
              c = g
            }
            if(c) {
              a.dispatchEvent("complete"), a.dispatchEvent("success")
            }else {
              a.gb = 6;
              var l;
              try {
                l = 2 < a.la() ? a.f.statusText : ""
              }catch(n) {
                a.a.j("Can not get status: " + n.message), l = ""
              }
              a.hb = l + " [" + ag(a) + "]";
              Yf(a)
            }
          }finally {
            Zf(a)
          }
        }
      }
    }
  }
}
function Zf(a, b) {
  if(a.f) {
    var c = a.f, d = a.$b[0] ? ea : k;
    a.f = k;
    a.$b = k;
    a.Ia && (Kb.clearTimeout(a.Ia), a.Ia = k);
    b || a.dispatchEvent("ready");
    try {
      c.onreadystatechange = d
    }catch(g) {
      a.a.H("Problem encountered resetting onreadystatechange: " + g.message)
    }
  }
}
q.la = function() {
  return this.f ? this.f.readyState : 0
};
function ag(a) {
  try {
    return 2 < a.la() ? a.f.status : -1
  }catch(b) {
    return a.a.q("Can not get status: " + b.message), -1
  }
}
q.getResponseHeader = function(a) {
  return this.f && 4 == this.la() ? this.f.getResponseHeader(a) : i
};
function Wf(a, b) {
  return b + " [" + a.Ed + " " + a.Kb + " " + ag(a) + "]"
}
;var bg = !(F || H && !I("420+"));
function cg(a, b) {
  this.Yb = a;
  this.R = b
}
C(cg, K);
q = cg.prototype;
q.i = k;
q.qa = -1;
q.ud = m;
q.xd = "Content-Length Server Date Expires Keep-Alive Content-Type Transfer-Encoding Cache-Control".split(" ");
function dg(a) {
  var b = ef(a.gd), c = b[0], b = b[1], d = t.parent;
  d ? (d.__XHRMaster_onframes(a.R, c, b), 1 != b && a.b()) : a.b()
}
q.Qe = function() {
  dg(this);
  if(!this.ja) {
    var a = t.parent;
    a && a.__XHRMaster_oncomplete(this.R);
    this.b()
  }
};
q.cf = function() {
  var a = t.parent;
  if(a) {
    this.qa = this.i.la();
    if(2 <= this.qa && !this.ud) {
      for(var b = new P, c = this.xd.length;c--;) {
        var d = this.xd[c];
        try {
          b.set(d, this.i.f.getResponseHeader(d))
        }catch(g) {
        }
      }
      if(b.A() && (this.ud = j, a.__XHRMaster_ongotheaders(this.R, rc(b)), this.ja)) {
        return
      }
    }
    a.__XHRMaster_onreadystatechange(this.R, this.qa);
    bg && 3 == this.qa && dg(this)
  }else {
    this.b()
  }
};
q.wc = function(a, b, c) {
  this.i = new Uf;
  Ab(this.i, "readystatechange", z(this.cf, this));
  Ab(this.i, "complete", z(this.Qe, this));
  this.i.send(a + "io/", b, c, {"Content-Type":"application/octet-stream"});
  this.gd = new df(this.i.f, 1048576)
};
q.d = function() {
  cg.n.d.call(this);
  delete this.gd;
  this.i && this.i.b();
  delete this.Yb.ob[this.R];
  delete this.Yb
};
function eg() {
  K.call(this);
  this.ob = {}
}
C(eg, K);
eg.prototype.Ve = function(a, b, c, d) {
  var g = new cg(this, a);
  this.ob[a] = g;
  g.wc(b, c, d)
};
eg.prototype.Ee = function(a) {
  (a = this.ob[a]) && a.b()
};
eg.prototype.d = function() {
  eg.n.d.call(this);
  for(var a = Za(this.ob);a.length;) {
    a.pop().b()
  }
  delete this.ob
};
var fg = new eg;
t.__XHRSlave_makeRequest = z(fg.Ve, fg);
t.__XHRSlave_dispose = z(fg.Ee, fg);
var gg = U("cw.net.demo");
function hg(a, b, c, d) {
  a = new Bd(document.location);
  if(c) {
    return new kf(d, a.ka, t.__demo_mainSocketPort)
  }
  b ? (b = t.__demo_shared_domain, w(b) || f(Error("domain was " + O(b) + "; expected a string.")), c = a.S(), Dd(c, "_____random_____." + b)) : c = a.S();
  Fd(c, d);
  Gd(c, "", i);
  return new mf(c.toString().replace("_____random_____", "%random%"))
}
;A("Minerva.HttpEndpoint", mf);
A("Minerva.SocketEndpoint", kf);
A("Minerva.QANHelper", R);
R.prototype.handleQANFrame = R.prototype.wd;
R.prototype.ask = R.prototype.qe;
R.prototype.notify = R.prototype.Ze;
R.prototype.failAll = R.prototype.nd;
A("Minerva.QANProtocolWrapper", rf);
rf.prototype.streamStarted = rf.prototype.of;
rf.prototype.streamReset = rf.prototype.nf;
rf.prototype.stringReceived = rf.prototype.pf;
A("Minerva.Deferred", M);
M.prototype.cancel = M.prototype.cancel;
M.prototype.callback = M.prototype.N;
M.prototype.errback = M.prototype.P;
M.prototype.addErrback = M.prototype.tb;
M.prototype.addCallback = M.prototype.Ma;
M.prototype.addCallbacks = M.prototype.Y;
M.prototype.chainDeferred = M.prototype.bd;
M.prototype.awaitDeferred = M.prototype.re;
M.prototype.branch = M.prototype.$c;
M.prototype.addBoth = M.prototype.Wc;
M.prototype.hasFired = M.prototype.Pe;
A("Minerva.Deferred.succeed", Rb);
A("Minerva.Deferred.fail", Sb);
A("Minerva.Deferred.cancelled", function() {
  var a = new M;
  a.cancel();
  return a
});
A("Minerva.Deferred.AlreadyCalledError", Pb);
A("Minerva.Deferred.CancelledError", Lb);
A("Minerva.ClientStream", $);
$.prototype.getUserContext = $.prototype.Ne;
$.prototype.bindToProtocol = $.prototype.se;
$.prototype.start = $.prototype.start;
$.prototype.sendString = $.prototype.de;
$.prototype.reset = $.prototype.reset;
$.prototype.dispose = $.prototype.b;
A("Minerva.Logger", S);
S.Level = T;
S.getLogger = U;
S.prototype.setLevel = S.prototype.Ic;
S.prototype.shout = S.prototype.jf;
S.prototype.severe = S.prototype.H;
S.prototype.warning = S.prototype.q;
S.prototype.info = S.prototype.info;
S.prototype.config = S.prototype.ye;
S.prototype.fine = S.prototype.j;
S.prototype.finer = S.prototype.Ie;
S.prototype.finest = S.prototype.s;
T.OFF = md;
T.SHOUT = nd;
T.SEVERE = od;
T.WARNING = pd;
T.INFO = qd;
T.CONFIG = rd;
T.FINE = sd;
T.FINER = td;
T.FINEST = ud;
T.ALL = vd;
A("Minerva.LogManager", V);
V.getRoot = V.pc;
A("Minerva.DivConsole", yd);
yd.prototype.setCapturing = yd.prototype.hf;
A("Minerva.JSON", {});
A("Minerva.JSON.parse", function(a) {
  a = String(a);
  if(/^\s*$/.test(a) ? 0 : /^[\],:{}\s\u2028\u2029]*$/.test(a.replace(/\\["\\\/bfnrtu]/g, "@").replace(/"[^"\\\n\r\u2028\u2029\x00-\x08\x10-\x1f]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, "]").replace(/(?:^|:|,)(?:[\s\u2028\u2029]*\[)+/g, ""))) {
    try {
      return eval("(" + a + ")")
    }catch(b) {
    }
  }
  f(Error("Invalid JSON string: " + a))
});
A("Minerva.JSON.serialize", Wb);
A("Minerva.JSON.asciify", Wb);
A("Minerva.bind", z);
A("Minerva.repr", O);
A("Minerva.theCallQueue", Ub);
A("Minerva.MINIMUM_FLASH_VERSION", "9");
A("Minerva.getEndpoint", hg);
A("Minerva.getEndpointByQueryArgs", function() {
  var a;
  a = (new Bd(document.location)).Q;
  var b = "http" != a.get("mode");
  if((a = Boolean(Number(a.get("useSubdomains", "0")))) && !t.__demo_shared_domain) {
    gg.q("You requested subdomains, but I cannot use them because you did not specify a domain.  Proceeding without subdomains."), a = m
  }
  return hg(0, a, b, "/_minerva/")
});

})();

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
function o(a) {
  return function() {
    return this[a]
  }
}
function ba(a) {
  return function() {
    return a
  }
}
var p;
var ca = ca || {}, s = this;
function da(a) {
  for(var a = a.split("."), b = s, c;c = a.shift();) {
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
function t(a) {
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
function u(a) {
  return a !== i
}
function fa(a) {
  return"array" == t(a)
}
function ga(a) {
  var b = t(a);
  return"array" == b || "object" == b && "number" == typeof a.length
}
function ha(a) {
  return ia(a) && "function" == typeof a.getFullYear
}
function v(a) {
  return"string" == typeof a
}
function ja(a) {
  return"function" == t(a)
}
function ia(a) {
  var b = typeof a;
  return"object" == b && a != k || "function" == b
}
function ka(a) {
  return a[la] || (a[la] = ++ma)
}
var la = "closure_uid_" + Math.floor(2147483648 * Math.random()).toString(36), ma = 0;
function na(a, b, c) {
  return a.call.apply(a.bind, arguments)
}
function oa(a, b, c) {
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
function x(a, b, c) {
  x = Function.prototype.bind && -1 != Function.prototype.bind.toString().indexOf("native code") ? na : oa;
  return x.apply(k, arguments)
}
var pa = Date.now || function() {
  return+new Date
};
function y(a, b) {
  var c = a.split("."), d = s;
  !(c[0] in d) && d.execScript && d.execScript("var " + c[0]);
  for(var g;c.length && (g = c.shift());) {
    !c.length && u(b) ? d[g] = b : d = d[g] ? d[g] : d[g] = {}
  }
}
function A(a, b) {
  function c() {
  }
  c.prototype = b.prototype;
  a.m = b.prototype;
  a.prototype = new c;
  a.prototype.constructor = a
}
;function B(a) {
  Error.captureStackTrace ? Error.captureStackTrace(this, B) : this.stack = Error().stack || "";
  a && (this.message = "" + a)
}
A(B, Error);
B.prototype.name = "CustomError";
function qa(a, b) {
  for(var c = 1;c < arguments.length;c++) {
    var d = ("" + arguments[c]).replace(/\$/g, "$$$$"), a = a.replace(/\%s/, d)
  }
  return a
}
function ra(a, b) {
  return a.replace(/(\r\n|\r|\n)/g, b ? "<br />" : "<br>")
}
function C(a) {
  if(!sa.test(a)) {
    return a
  }
  -1 != a.indexOf("&") && (a = a.replace(ta, "&amp;"));
  -1 != a.indexOf("<") && (a = a.replace(ua, "&lt;"));
  -1 != a.indexOf(">") && (a = a.replace(va, "&gt;"));
  -1 != a.indexOf('"') && (a = a.replace(wa, "&quot;"));
  return a
}
var ta = /&/g, ua = /</g, va = />/g, wa = /\"/g, sa = /[&<>\"]/;
function xa(a) {
  return ra(a.replace(/  /g, " &#160;"), i)
}
function ya(a, b) {
  for(var c = 0, d = ("" + a).replace(/^[\s\xa0]+|[\s\xa0]+$/g, "").split("."), g = ("" + b).replace(/^[\s\xa0]+|[\s\xa0]+$/g, "").split("."), e = Math.max(d.length, g.length), h = 0;0 == c && h < e;h++) {
    var l = d[h] || "", n = g[h] || "", q = RegExp("(\\d*)(\\D*)", "g"), z = RegExp("(\\d*)(\\D*)", "g");
    do {
      var r = q.exec(l) || ["", "", ""], w = z.exec(n) || ["", "", ""];
      if(0 == r[0].length && 0 == w[0].length) {
        break
      }
      c = ((0 == r[1].length ? 0 : parseInt(r[1], 10)) < (0 == w[1].length ? 0 : parseInt(w[1], 10)) ? -1 : (0 == r[1].length ? 0 : parseInt(r[1], 10)) > (0 == w[1].length ? 0 : parseInt(w[1], 10)) ? 1 : 0) || ((0 == r[2].length) < (0 == w[2].length) ? -1 : (0 == r[2].length) > (0 == w[2].length) ? 1 : 0) || (r[2] < w[2] ? -1 : r[2] > w[2] ? 1 : 0)
    }while(0 == c)
  }
  return c
}
;function za(a, b) {
  b.unshift(a);
  B.call(this, qa.apply(k, b));
  b.shift()
}
A(za, B);
za.prototype.name = "AssertionError";
function Aa(a, b) {
  f(new za("Failure" + (a ? ": " + a : ""), Array.prototype.slice.call(arguments, 1)))
}
;var Ba;
Ba = ba(j);
var Ca, Da, Ea, Fa;
function Ga() {
  return s.navigator ? s.navigator.userAgent : k
}
Fa = Ea = Da = Ca = m;
var Ha;
if(Ha = Ga()) {
  var Ia = s.navigator;
  Ca = 0 == Ha.indexOf("Opera");
  Da = !Ca && -1 != Ha.indexOf("MSIE");
  Ea = !Ca && -1 != Ha.indexOf("WebKit");
  Fa = !Ca && !Ea && "Gecko" == Ia.product
}
var Ja = Ca, D = Da, Ka = Fa, F = Ea, La;
a: {
  var Ma = "", Na;
  if(Ja && s.opera) {
    var Oa = s.opera.version, Ma = "function" == typeof Oa ? Oa() : Oa
  }else {
    if(Ka ? Na = /rv\:([^\);]+)(\)|;)/ : D ? Na = /MSIE\s+([^\);]+)(\)|;)/ : F && (Na = /WebKit\/(\S+)/), Na) {
      var Pa = Na.exec(Ga()), Ma = Pa ? Pa[1] : ""
    }
  }
  if(D) {
    var Qa, Ra = s.document;
    Qa = Ra ? Ra.documentMode : i;
    if(Qa > parseFloat(Ma)) {
      La = "" + Qa;
      break a
    }
  }
  La = Ma
}
var Sa = {};
function G(a) {
  return Sa[a] || (Sa[a] = 0 <= ya(La, a))
}
var Ta = {};
function Ua() {
  return Ta[9] || (Ta[9] = D && !!document.documentMode && 9 <= document.documentMode)
}
;function Va() {
}
var Wa = 0;
p = Va.prototype;
p.key = 0;
p.Wa = m;
p.ac = m;
p.Hb = function(a, b, c, d, g, e) {
  ja(a) ? this.Ad = j : a && a.handleEvent && ja(a.handleEvent) ? this.Ad = m : f(Error("Invalid listener argument"));
  this.hb = a;
  this.Rd = b;
  this.src = c;
  this.type = d;
  this.capture = !!g;
  this.oc = e;
  this.ac = m;
  this.key = ++Wa;
  this.Wa = m
};
p.handleEvent = function(a) {
  return this.Ad ? this.hb.call(this.oc || this.src, a) : this.hb.handleEvent.call(this.hb, a)
};
function Xa(a, b) {
  for(var c in a) {
    b.call(i, a[c], c, a)
  }
}
function Ya(a) {
  var b = [], c = 0, d;
  for(d in a) {
    b[c++] = a[d]
  }
  return b
}
function Za(a) {
  var b = [], c = 0, d;
  for(d in a) {
    b[c++] = d
  }
  return b
}
var $a = "constructor hasOwnProperty isPrototypeOf propertyIsEnumerable toLocaleString toString valueOf".split(" ");
function ab(a, b) {
  for(var c, d, g = 1;g < arguments.length;g++) {
    d = arguments[g];
    for(c in d) {
      a[c] = d[c]
    }
    for(var e = 0;e < $a.length;e++) {
      c = $a[e], Object.prototype.hasOwnProperty.call(d, c) && (a[c] = d[c])
    }
  }
}
;!D || Ua();
var bb = !D || Ua(), cb = D && !G("8");
!F || G("528");
Ka && G("1.9b") || D && G("8") || Ja && G("9.5") || F && G("528");
Ka && !G("8") || D && G("9");
var H = Array.prototype, db = H.indexOf ? function(a, b, c) {
  return H.indexOf.call(a, b, c)
} : function(a, b, c) {
  c = c == k ? 0 : 0 > c ? Math.max(0, a.length + c) : c;
  if(v(a)) {
    return!v(b) || 1 != b.length ? -1 : a.indexOf(b, c)
  }
  for(;c < a.length;c++) {
    if(c in a && a[c] === b) {
      return c
    }
  }
  return-1
}, eb = H.forEach ? function(a, b, c) {
  H.forEach.call(a, b, c)
} : function(a, b, c) {
  for(var d = a.length, g = v(a) ? a.split("") : a, e = 0;e < d;e++) {
    e in g && b.call(c, g[e], e, a)
  }
}, fb = H.map ? function(a, b, c) {
  return H.map.call(a, b, c)
} : function(a, b, c) {
  for(var d = a.length, g = Array(d), e = v(a) ? a.split("") : a, h = 0;h < d;h++) {
    h in e && (g[h] = b.call(c, e[h], h, a))
  }
  return g
}, gb = H.some ? function(a, b, c) {
  return H.some.call(a, b, c)
} : function(a, b, c) {
  for(var d = a.length, g = v(a) ? a.split("") : a, e = 0;e < d;e++) {
    if(e in g && b.call(c, g[e], e, a)) {
      return j
    }
  }
  return m
}, hb = H.every ? function(a, b, c) {
  return H.every.call(a, b, c)
} : function(a, b, c) {
  for(var d = a.length, g = v(a) ? a.split("") : a, e = 0;e < d;e++) {
    if(e in g && !b.call(c, g[e], e, a)) {
      return m
    }
  }
  return j
};
function ib(a, b) {
  var c = db(a, b);
  0 <= c && H.splice.call(a, c, 1)
}
function jb(a) {
  return H.concat.apply(H, arguments)
}
function kb(a, b, c) {
  return 2 >= arguments.length ? H.slice.call(a, b) : H.slice.call(a, b, c)
}
function lb(a, b) {
  return a > b ? 1 : a < b ? -1 : 0
}
;var mb = {yf:"click", Df:"dblclick", Xf:"mousedown", ag:"mouseup", $f:"mouseover", Zf:"mouseout", Yf:"mousemove", mg:"selectstart", Sf:"keypress", Rf:"keydown", Tf:"keyup", wf:"blur", Lf:"focus", Ef:"deactivate", Mf:D ? "focusin" : "DOMFocusIn", Nf:D ? "focusout" : "DOMFocusOut", xf:"change", lg:"select", ng:"submit", Qf:"input", hg:"propertychange", If:"dragstart", Ff:"dragenter", Hf:"dragover", Gf:"dragleave", Jf:"drop", rg:"touchstart", qg:"touchmove", pg:"touchend", og:"touchcancel", Af:"contextmenu", 
Kf:"error", Pf:"help", Uf:"load", Vf:"losecapture", ig:"readystatechange", jg:"resize", kg:"scroll", tg:"unload", Of:"hashchange", dg:"pagehide", eg:"pageshow", gg:"popstate", Bf:"copy", fg:"paste", Cf:"cut", tf:"beforecopy", uf:"beforecut", vf:"beforepaste", cg:"online", bg:"offline", Wf:"message", zf:"connect", sg:F ? "webkitTransitionEnd" : Ja ? "oTransitionEnd" : "transitionend"};
function I() {
}
I.prototype.ja = m;
I.prototype.b = function() {
  this.ja || (this.ja = j, this.d())
};
I.prototype.d = function() {
  this.xe && nb.apply(k, this.xe)
};
function nb(a) {
  for(var b = 0, c = arguments.length;b < c;++b) {
    var d = arguments[b];
    ga(d) ? nb.apply(k, d) : d && "function" == typeof d.b && d.b()
  }
}
;function ob(a, b) {
  this.type = a;
  this.currentTarget = this.target = b
}
A(ob, I);
p = ob.prototype;
p.d = function() {
  delete this.type;
  delete this.target;
  delete this.currentTarget
};
p.Fa = m;
p.defaultPrevented = m;
p.Sb = j;
p.stopPropagation = function() {
  this.Fa = j
};
p.preventDefault = function() {
  this.defaultPrevented = j;
  this.Sb = m
};
function pb(a) {
  a.stopPropagation()
}
;function qb(a) {
  qb[" "](a);
  return a
}
qb[" "] = ea;
function rb(a, b) {
  a && this.Hb(a, b)
}
A(rb, ob);
p = rb.prototype;
p.target = k;
p.relatedTarget = k;
p.offsetX = 0;
p.offsetY = 0;
p.clientX = 0;
p.clientY = 0;
p.screenX = 0;
p.screenY = 0;
p.button = 0;
p.keyCode = 0;
p.charCode = 0;
p.ctrlKey = m;
p.altKey = m;
p.shiftKey = m;
p.metaKey = m;
p.Ma = k;
p.Hb = function(a, b) {
  var c = this.type = a.type;
  ob.call(this, c);
  this.target = a.target || a.srcElement;
  this.currentTarget = b;
  var d = a.relatedTarget;
  if(d) {
    if(Ka) {
      var g;
      a: {
        try {
          qb(d.nodeName);
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
  this.offsetX = F || a.offsetX !== i ? a.offsetX : a.layerX;
  this.offsetY = F || a.offsetY !== i ? a.offsetY : a.layerY;
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
  this.state = a.state;
  this.Ma = a;
  a.defaultPrevented && this.preventDefault();
  delete this.Fa
};
p.stopPropagation = function() {
  rb.m.stopPropagation.call(this);
  this.Ma.stopPropagation ? this.Ma.stopPropagation() : this.Ma.cancelBubble = j
};
p.preventDefault = function() {
  rb.m.preventDefault.call(this);
  var a = this.Ma;
  if(a.preventDefault) {
    a.preventDefault()
  }else {
    if(a.returnValue = m, cb) {
      try {
        if(a.ctrlKey || 112 <= a.keyCode && 123 >= a.keyCode) {
          a.keyCode = -1
        }
      }catch(b) {
      }
    }
  }
};
p.d = function() {
  rb.m.d.call(this);
  this.relatedTarget = this.currentTarget = this.target = this.Ma = k
};
var sb = {}, J = {}, K = {}, tb = {};
function ub(a, b, c, d, g) {
  if(b) {
    if(fa(b)) {
      for(var e = 0;e < b.length;e++) {
        ub(a, b[e], c, d, g)
      }
      return k
    }
    var d = !!d, h = J;
    b in h || (h[b] = {c:0, M:0});
    h = h[b];
    d in h || (h[d] = {c:0, M:0}, h.c++);
    var h = h[d], l = ka(a), n;
    h.M++;
    if(h[l]) {
      n = h[l];
      for(e = 0;e < n.length;e++) {
        if(h = n[e], h.hb == c && h.oc == g) {
          if(h.Wa) {
            break
          }
          return n[e].key
        }
      }
    }else {
      n = h[l] = [], h.c++
    }
    var q = vb, z = bb ? function(a) {
      return q.call(z.src, z.key, a)
    } : function(a) {
      a = q.call(z.src, z.key, a);
      if(!a) {
        return a
      }
    }, e = z;
    e.src = a;
    h = new Va;
    h.Hb(c, e, a, b, d, g);
    c = h.key;
    e.key = c;
    n.push(h);
    sb[c] = h;
    K[l] || (K[l] = []);
    K[l].push(h);
    a.addEventListener ? (a == s || !a.ed) && a.addEventListener(b, e, d) : a.attachEvent(b in tb ? tb[b] : tb[b] = "on" + b, e);
    return c
  }
  f(Error("Invalid event type"))
}
function wb(a, b, c, d, g) {
  if(fa(b)) {
    for(var e = 0;e < b.length;e++) {
      wb(a, b[e], c, d, g)
    }
    return k
  }
  a = ub(a, b, c, d, g);
  sb[a].ac = j;
  return a
}
function xb(a, b, c, d, g) {
  if(fa(b)) {
    for(var e = 0;e < b.length;e++) {
      xb(a, b[e], c, d, g)
    }
  }else {
    d = !!d;
    a: {
      e = J;
      if(b in e && (e = e[b], d in e && (e = e[d], a = ka(a), e[a]))) {
        a = e[a];
        break a
      }
      a = k
    }
    if(a) {
      for(e = 0;e < a.length;e++) {
        if(a[e].hb == c && a[e].capture == d && a[e].oc == g) {
          yb(a[e].key);
          break
        }
      }
    }
  }
}
function yb(a) {
  if(!sb[a]) {
    return m
  }
  var b = sb[a];
  if(b.Wa) {
    return m
  }
  var c = b.src, d = b.type, g = b.Rd, e = b.capture;
  c.removeEventListener ? (c == s || !c.ed) && c.removeEventListener(d, g, e) : c.detachEvent && c.detachEvent(d in tb ? tb[d] : tb[d] = "on" + d, g);
  c = ka(c);
  g = J[d][e][c];
  if(K[c]) {
    var h = K[c];
    ib(h, b);
    0 == h.length && delete K[c]
  }
  b.Wa = j;
  g.Ld = j;
  zb(d, e, c, g);
  delete sb[a];
  return j
}
function zb(a, b, c, d) {
  if(!d.Jb && d.Ld) {
    for(var g = 0, e = 0;g < d.length;g++) {
      d[g].Wa ? d[g].Rd.src = k : (g != e && (d[e] = d[g]), e++)
    }
    d.length = e;
    d.Ld = m;
    0 == e && (delete J[a][b][c], J[a][b].c--, 0 == J[a][b].c && (delete J[a][b], J[a].c--), 0 == J[a].c && delete J[a])
  }
}
function Ab(a, b, c, d, g) {
  var e = 1, b = ka(b);
  if(a[b]) {
    a.M--;
    a = a[b];
    a.Jb ? a.Jb++ : a.Jb = 1;
    try {
      for(var h = a.length, l = 0;l < h;l++) {
        var n = a[l];
        n && !n.Wa && (e &= Bb(n, g) !== m)
      }
    }finally {
      a.Jb--, zb(c, d, b, a)
    }
  }
  return Boolean(e)
}
function Bb(a, b) {
  var c = a.handleEvent(b);
  a.ac && yb(a.key);
  return c
}
function vb(a, b) {
  if(!sb[a]) {
    return j
  }
  var c = sb[a], d = c.type, g = J;
  if(!(d in g)) {
    return j
  }
  var g = g[d], e, h;
  if(!bb) {
    e = b || da("window.event");
    var l = j in g, n = m in g;
    if(l) {
      if(0 > e.keyCode || e.returnValue != i) {
        return j
      }
      a: {
        var q = m;
        if(0 == e.keyCode) {
          try {
            e.keyCode = -1;
            break a
          }catch(z) {
            q = j
          }
        }
        if(q || e.returnValue == i) {
          e.returnValue = j
        }
      }
    }
    q = new rb;
    q.Hb(e, this);
    e = j;
    try {
      if(l) {
        for(var r = [], w = q.currentTarget;w;w = w.parentNode) {
          r.push(w)
        }
        h = g[j];
        h.M = h.c;
        for(var E = r.length - 1;!q.Fa && 0 <= E && h.M;E--) {
          q.currentTarget = r[E], e &= Ab(h, r[E], d, j, q)
        }
        if(n) {
          h = g[m];
          h.M = h.c;
          for(E = 0;!q.Fa && E < r.length && h.M;E++) {
            q.currentTarget = r[E], e &= Ab(h, r[E], d, m, q)
          }
        }
      }else {
        e = Bb(c, q)
      }
    }finally {
      r && (r.length = 0), q.b()
    }
    return e
  }
  d = new rb(b, this);
  try {
    e = Bb(c, d)
  }finally {
    d.b()
  }
  return e
}
var Cb = 0;
function Db() {
}
A(Db, I);
p = Db.prototype;
p.ed = j;
p.Mb = k;
p.Jc = aa("Mb");
p.addEventListener = function(a, b, c, d) {
  ub(this, a, b, c, d)
};
p.removeEventListener = function(a, b, c, d) {
  xb(this, a, b, c, d)
};
p.dispatchEvent = function(a) {
  var b = a.type || a, c = J;
  if(b in c) {
    if(v(a)) {
      a = new ob(a, this)
    }else {
      if(a instanceof ob) {
        a.target = a.target || this
      }else {
        var d = a, a = new ob(b, this);
        ab(a, d)
      }
    }
    var d = 1, g, c = c[b], b = j in c, e;
    if(b) {
      g = [];
      for(e = this;e;e = e.Mb) {
        g.push(e)
      }
      e = c[j];
      e.M = e.c;
      for(var h = g.length - 1;!a.Fa && 0 <= h && e.M;h--) {
        a.currentTarget = g[h], d &= Ab(e, g[h], a.type, j, a) && a.Sb != m
      }
    }
    if(m in c) {
      if(e = c[m], e.M = e.c, b) {
        for(h = 0;!a.Fa && h < g.length && e.M;h++) {
          a.currentTarget = g[h], d &= Ab(e, g[h], a.type, m, a) && a.Sb != m
        }
      }else {
        for(g = this;!a.Fa && g && e.M;g = g.Mb) {
          a.currentTarget = g, d &= Ab(e, g, a.type, m, a) && a.Sb != m
        }
      }
    }
    a = Boolean(d)
  }else {
    a = j
  }
  return a
};
p.d = function() {
  Db.m.d.call(this);
  var a, b = 0, c = a == k;
  a = !!a;
  if(this == k) {
    Xa(K, function(d) {
      for(var e = d.length - 1;0 <= e;e--) {
        var g = d[e];
        if(c || a == g.capture) {
          yb(g.key), b++
        }
      }
    })
  }else {
    var d = ka(this);
    if(K[d]) {
      for(var d = K[d], g = d.length - 1;0 <= g;g--) {
        var e = d[g];
        if(c || a == e.capture) {
          yb(e.key), b++
        }
      }
    }
  }
  this.Mb = k
};
var Eb = s.window;
Cb++;
Cb++;
/*
 Portions of this code are from MochiKit, received by
 The Closure Authors under the MIT license. All other code is Copyright
 2005-2009 The Closure Authors. All Rights Reserved.
*/
function L(a, b) {
  this.vb = [];
  this.$c = a;
  this.gd = b || k
}
p = L.prototype;
p.$ = m;
p.cb = m;
p.jb = 0;
p.Kc = m;
p.se = m;
p.tb = 0;
p.cancel = function(a) {
  if(this.$) {
    this.lb instanceof L && this.lb.cancel()
  }else {
    if(this.t) {
      var b = this.t;
      delete this.t;
      a ? b.cancel(a) : (b.tb--, 0 >= b.tb && b.cancel())
    }
    this.$c ? this.$c.call(this.gd, this) : this.Kc = j;
    this.$ || this.P(new Fb)
  }
};
p.cd = function(a, b) {
  Gb(this, a, b);
  this.jb--;
  0 == this.jb && this.$ && Hb(this)
};
function Gb(a, b, c) {
  a.$ = j;
  a.lb = c;
  a.cb = !b;
  Hb(a)
}
function Ib(a) {
  a.$ && (a.Kc || f(new Jb), a.Kc = m)
}
p.N = function(a) {
  Ib(this);
  Gb(this, j, a)
};
p.P = function(a) {
  Ib(this);
  Gb(this, m, a)
};
p.La = function(a, b) {
  return this.Y(a, k, b)
};
p.sb = function(a, b) {
  return this.Y(k, a, b)
};
p.Y = function(a, b, c) {
  this.vb.push([a, b, c]);
  this.$ && Hb(this);
  return this
};
p.ad = function(a) {
  this.Y(a.N, a.P, a);
  return this
};
p.ne = function(a) {
  return this.La(x(a.Zc, a))
};
p.Zc = function(a) {
  var b = new L;
  this.ad(b);
  a && (b.t = this, this.tb++);
  return b
};
p.Vc = function(a, b) {
  return this.Y(a, a, b)
};
p.Ke = o("$");
function Kb(a) {
  return gb(a.vb, function(a) {
    return ja(a[1])
  })
}
function Hb(a) {
  a.Tc && (a.$ && Kb(a)) && (s.clearTimeout(a.Tc), delete a.Tc);
  a.t && (a.t.tb--, delete a.t);
  for(var b = a.lb, c = m, d = m;a.vb.length && 0 == a.jb;) {
    var g = a.vb.shift(), e = g[0], h = g[1], g = g[2];
    if(e = a.cb ? h : e) {
      try {
        var l = e.call(g || a.gd, b);
        u(l) && (a.cb = a.cb && (l == b || l instanceof Error), a.lb = b = l);
        b instanceof L && (d = j, a.jb++)
      }catch(n) {
        b = n, a.cb = j, Kb(a) || (c = j)
      }
    }
  }
  a.lb = b;
  d && a.jb && (b.Y(x(a.cd, a, j), x(a.cd, a, m)), b.se = j);
  c && (a.Tc = s.setTimeout(function() {
    f(new Lb(b))
  }, 0))
}
function Mb(a) {
  var b = new L;
  b.N(a);
  return b
}
function Nb(a) {
  var b = new L;
  b.P(a);
  return b
}
function Jb() {
  B.call(this)
}
A(Jb, B);
Jb.prototype.message = "Already called";
function Fb() {
  B.call(this)
}
A(Fb, B);
Fb.prototype.message = "Deferred was cancelled";
function Lb(a) {
  B.call(this);
  this.message = "Unhandled Error in Deferred: " + (a.message || "[No message]")
}
A(Lb, B);
function Ob(a) {
  this.z = a;
  this.zb = [];
  this.kd = [];
  this.re = x(this.mf, this)
}
Ob.prototype.Qc = k;
Ob.prototype.mf = function() {
  this.Qc = k;
  var a = this.zb;
  this.zb = [];
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
  if(0 == this.zb.length) {
    a = this.kd;
    this.kd = [];
    for(b = 0;b < a.length;b++) {
      a[b].N(k)
    }
  }
};
var Pb = new Ob(s.window);
function Qb(a) {
  return ja(a) || "object" == typeof a && ja(a.call) && ja(a.apply)
}
;function Rb(a, b) {
  var c = [];
  Sb(new Tb(b), a, c);
  return c.join("")
}
function Tb(a) {
  this.Rb = a
}
function Sb(a, b, c) {
  switch(typeof b) {
    case "string":
      Ub(b, c);
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
          c.push(g), g = b[e], Sb(a, a.Rb ? a.Rb.call(b, "" + e, g) : g, c), g = ","
        }
        c.push("]");
        break
      }
      c.push("{");
      d = "";
      for(e in b) {
        Object.prototype.hasOwnProperty.call(b, e) && (g = b[e], "function" != typeof g && (c.push(d), Ub(e, c), c.push(":"), Sb(a, a.Rb ? a.Rb.call(b, e, g) : g, c), d = ","))
      }
      c.push("}");
      break;
    case "function":
      break;
    default:
      f(Error("Unknown type: " + typeof b))
  }
}
var Vb = {'"':'\\"', "\\":"\\\\", "/":"\\/", "\b":"\\b", "\f":"\\f", "\n":"\\n", "\r":"\\r", "\t":"\\t", "\x0B":"\\u000b"}, Wb = /\uffff/.test("\uffff") ? /[\\\"\x00-\x1f\x7f-\uffff]/g : /[\\\"\x00-\x1f\x7f-\xff]/g;
function Ub(a, b) {
  b.push('"', a.replace(Wb, function(a) {
    if(a in Vb) {
      return Vb[a]
    }
    var b = a.charCodeAt(0), g = "\\u";
    16 > b ? g += "000" : 256 > b ? g += "00" : 4096 > b && (g += "0");
    return Vb[a] = g + b.toString(16)
  }), '"')
}
;function Xb(a, b, c) {
  var d = db(c, a);
  if(-1 != d) {
    b.push("#CYCLETO:" + (c.length - d) + "#")
  }else {
    c.push(a);
    d = t(a);
    if("boolean" == d || "number" == d || "null" == d || "undefined" == d) {
      b.push("" + a)
    }else {
      if("string" == d) {
        Ub(a, b)
      }else {
        if(Qb(a.v)) {
          a.v(b, c)
        }else {
          if(Qb(a.je)) {
            b.push("<cw.eq.Wildcard>")
          }else {
            if(a instanceof RegExp) {
              b.push(a.toString())
            }else {
              if("array" == d) {
                d = a.length;
                b.push("[");
                for(var g = "", e = 0;e < d;e++) {
                  b.push(g), Xb(a[e], b, c), g = ", "
                }
                b.push("]")
              }else {
                if("object" == d) {
                  if(ha(a) && "function" == typeof a.valueOf) {
                    b.push("new Date(", "" + a.valueOf(), ")")
                  }else {
                    for(var d = Za(a).concat($a), g = {}, h = e = 0;h < d.length;) {
                      var l = d[h++], n = ia(l) ? "o" + ka(l) : (typeof l).charAt(0) + l;
                      Object.prototype.hasOwnProperty.call(g, n) || (g[n] = j, d[e++] = l)
                    }
                    d.length = e;
                    b.push("{");
                    g = "";
                    for(h = 0;h < d.length;h++) {
                      e = d[h], Object.prototype.hasOwnProperty.call(a, e) && (l = a[e], b.push(g), Ub(e, b), b.push(": "), Xb(l, b, c), g = ", ")
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
function M(a, b, c) {
  c || (c = []);
  Xb(a, b, c)
}
function N(a, b) {
  var c = [];
  M(a, c, b);
  return c.join("")
}
;function Yb() {
  return Math.floor(2147483648 * Math.random()).toString(36) + Math.abs(Math.floor(2147483648 * Math.random()) ^ pa()).toString(36)
}
function Zb(a) {
  return a.substr(0, a.length - 1)
}
var $b = /^(0|[1-9]\d*)$/, ac = /^(0|\-?[1-9]\d*)$/;
function bc(a) {
  var b = cc;
  return $b.test(a) && (a = parseInt(a, 10), a <= b) ? a : k
}
;var cc = Math.pow(2, 53);
function dc(a) {
  if("function" == typeof a.A) {
    a = a.A()
  }else {
    if(ga(a) || v(a)) {
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
function ec(a) {
  if("function" == typeof a.C) {
    return a.C()
  }
  if(v(a)) {
    return a.split("")
  }
  if(ga(a)) {
    for(var b = [], c = a.length, d = 0;d < c;d++) {
      b.push(a[d])
    }
    return b
  }
  return Ya(a)
}
function fc(a) {
  if("function" == typeof a.T) {
    return a.T()
  }
  if("function" != typeof a.C) {
    if(ga(a) || v(a)) {
      for(var b = [], a = a.length, c = 0;c < a;c++) {
        b.push(c)
      }
      return b
    }
    return Za(a)
  }
}
function gc(a, b, c) {
  if("function" == typeof a.forEach) {
    a.forEach(b, c)
  }else {
    if(ga(a) || v(a)) {
      eb(a, b, c)
    }else {
      for(var d = fc(a), g = ec(a), e = g.length, h = 0;h < e;h++) {
        b.call(c, g[h], d && d[h], a)
      }
    }
  }
}
function hc(a, b) {
  if("function" == typeof a.every) {
    return a.every(b, i)
  }
  if(ga(a) || v(a)) {
    return hb(a, b, i)
  }
  for(var c = fc(a), d = ec(a), g = d.length, e = 0;e < g;e++) {
    if(!b.call(i, d[e], c && c[e], a)) {
      return m
    }
  }
  return j
}
;function O(a, b) {
  this.n = {};
  this.g = [];
  var c = arguments.length;
  if(1 < c) {
    c % 2 && f(Error("Uneven number of arguments"));
    for(var d = 0;d < c;d += 2) {
      this.set(arguments[d], arguments[d + 1])
    }
  }else {
    a && this.$b(a)
  }
}
p = O.prototype;
p.c = 0;
p.A = o("c");
p.C = function() {
  ic(this);
  for(var a = [], b = 0;b < this.g.length;b++) {
    a.push(this.n[this.g[b]])
  }
  return a
};
p.T = function() {
  ic(this);
  return this.g.concat()
};
p.Z = function(a) {
  return jc(this.n, a)
};
p.dc = function(a) {
  for(var b = 0;b < this.g.length;b++) {
    var c = this.g[b];
    if(jc(this.n, c) && this.n[c] == a) {
      return j
    }
  }
  return m
};
p.K = function(a, b) {
  if(this === a) {
    return j
  }
  if(this.c != a.A()) {
    return m
  }
  var c = b || kc;
  ic(this);
  for(var d, g = 0;d = this.g[g];g++) {
    if(!c(this.get(d), a.get(d))) {
      return m
    }
  }
  return j
};
function kc(a, b) {
  return a === b
}
p.fb = function() {
  return 0 == this.c
};
p.clear = function() {
  this.n = {};
  this.c = this.g.length = 0
};
p.remove = function(a) {
  return jc(this.n, a) ? (delete this.n[a], this.c--, this.g.length > 2 * this.c && ic(this), j) : m
};
function ic(a) {
  if(a.c != a.g.length) {
    for(var b = 0, c = 0;b < a.g.length;) {
      var d = a.g[b];
      jc(a.n, d) && (a.g[c++] = d);
      b++
    }
    a.g.length = c
  }
  if(a.c != a.g.length) {
    for(var g = {}, c = b = 0;b < a.g.length;) {
      d = a.g[b], jc(g, d) || (a.g[c++] = d, g[d] = 1), b++
    }
    a.g.length = c
  }
}
p.get = function(a, b) {
  return jc(this.n, a) ? this.n[a] : b
};
p.set = function(a, b) {
  jc(this.n, a) || (this.c++, this.g.push(a));
  this.n[a] = b
};
p.$b = function(a) {
  var b;
  a instanceof O ? (b = a.T(), a = a.C()) : (b = Za(a), a = Ya(a));
  for(var c = 0;c < b.length;c++) {
    this.set(b[c], a[c])
  }
};
p.S = function() {
  return new O(this)
};
function mc(a) {
  ic(a);
  for(var b = {}, c = 0;c < a.g.length;c++) {
    var d = a.g[c];
    b[d] = a.n[d]
  }
  return b
}
function jc(a, b) {
  return Object.prototype.hasOwnProperty.call(a, b)
}
;var nc = {je:ba("<cw.eq.Wildcard>")};
function oc(a) {
  return"boolean" == a || "number" == a || "null" == a || "undefined" == a || "string" == a
}
function pc(a, b, c) {
  var d = t(a), g = t(b);
  if(a == nc || b == nc) {
    return j
  }
  if(a != k && "function" == typeof a.K) {
    return c && c.push("running custom equals function on left object"), a.K(b, c)
  }
  if(b != k && "function" == typeof b.K) {
    return c && c.push("running custom equals function on right object"), b.K(a, c)
  }
  if(oc(d) || oc(g)) {
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
                if(!pc(a[d], b[d], c)) {
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
          if(a.ie == Ba && b.ie == Ba) {
            a: {
              c && c.push("descending into object");
              for(var e in a) {
                if(!(e in b)) {
                  c && c.push("property " + e + " missing on right object");
                  a = m;
                  break a
                }
                if(!pc(a[e], b[e], c)) {
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
;function P(a, b) {
  this.Xe = a;
  this.Pb = b
}
P.prototype.K = function(a, b) {
  return ia(a) && this.constructor == a.constructor && pc(this.Pb, a.Pb, b)
};
P.prototype.v = function(a, b) {
  a.push("new ", this.Xe, "(");
  for(var c = "", d = 0;d < this.Pb.length;d++) {
    a.push(c), c = ", ", M(this.Pb[d], a, b)
  }
  a.push(")")
};
var qc, rc;
function sc(a, b) {
  P.call(this, "Question", [a, b]);
  this.body = a;
  this.ca = b
}
A(sc, P);
function tc(a, b) {
  P.call(this, "OkayAnswer", [a, b]);
  this.body = a;
  this.ca = b
}
A(tc, P);
function uc(a, b) {
  P.call(this, "KnownErrorAnswer", [a, b]);
  this.body = a;
  this.ca = b
}
A(uc, P);
function vc(a, b) {
  P.call(this, "UnknownErrorAnswer", [a, b]);
  this.body = a;
  this.ca = b
}
A(vc, P);
function wc(a) {
  P.call(this, "Cancellation", [a]);
  this.ca = a
}
A(wc, P);
function xc(a) {
  P.call(this, "Notification", [a]);
  this.body = a
}
A(xc, P);
function yc(a) {
  if(a instanceof sc) {
    return"Q"
  }
  if(a instanceof tc) {
    return"K"
  }
  if(a instanceof uc) {
    return"E"
  }
  if(a instanceof vc) {
    return"U"
  }
  if(a instanceof wc) {
    return"C"
  }
  if(a instanceof xc) {
    return"#"
  }
  f(Error("qanTypeToCode bug"))
}
function zc(a) {
  var b = yc(a);
  if(a instanceof wc) {
    return"" + a.ca + b
  }
  v(a.body) || f(Error("qanFrame.body must be a string, was " + N(a.body)));
  return a instanceof xc ? a.body + b : a.body + "|" + ("" + a.ca) + b
}
function Ac(a) {
  B.call(this);
  this.message = a
}
A(Ac, B);
function Bc(a) {
  a = bc(a);
  a === k && f(new Ac("bad qid"));
  return a
}
function Cc(a) {
  a || f(new Ac("0-length frame"));
  var b = a.substr(a.length - 1, 1);
  if("#" == b) {
    return new xc(Zb(a))
  }
  if("C" == b) {
    var c = Bc(Zb(a));
    return new wc(c)
  }
  a = a.split("|");
  c = a.splice(a.length - 1, a.length);
  0 < a.length && c.splice(0, 0, a.join("|"));
  a = c[0];
  c = c[1];
  u(c) || f(new Ac("Expected pipe char in frame"));
  c = Bc(Zb(c));
  if("Q" == b) {
    return new sc(a, c)
  }
  if("K" == b) {
    return new tc(a, c)
  }
  if("E" == b) {
    return new uc(a, c)
  }
  if("U" == b) {
    return new vc(a, c)
  }
  f(new Ac("Invalid QAN frame type " + N(b)))
}
function Dc(a) {
  B.call(this);
  this.body = a
}
A(Dc, B);
Dc.prototype.message = "KnownError with arbitrary body";
Dc.prototype.v = function(a, b) {
  a.push("new KnownError(");
  M(this.body, a, b);
  a.push(")")
};
function Ec(a) {
  B.call(this);
  this.body = a
}
A(Ec, B);
Ec.prototype.message = "UnknownError with arbitrary body";
Ec.prototype.v = function(a, b) {
  a.push("new UnknownError(");
  M(this.body, a, b);
  a.push(")")
};
function Fc(a) {
  B.call(this);
  this.message = a
}
A(Fc, B);
function Q(a, b, c, d) {
  this.Yc = a;
  this.ib = b;
  this.da = c;
  this.Bb = d;
  this.Ob = 0;
  this.ma = new O;
  this.Za = new O
}
p = Q.prototype;
p.v = function(a) {
  a.push("<QANHelper asked ", "" + this.Ob, " questions, waiting for ", "" + this.ma.A(), " peer answers and ", "" + this.Za.A(), " local answers>")
};
p.ud = function(a) {
  if(a instanceof tc || a instanceof uc || a instanceof vc) {
    var b = a.ca, c = this.ma.get(b);
    this.ma.remove(b);
    u(c) ? c !== k && (a instanceof tc ? c.N(a.body) : a instanceof uc ? c.P(new Dc(a.body)) : a instanceof vc ? c.P(new Ec(a.body)) : f(Error("handleQANFrame bug"))) : this.Bb("Received an answer with invalid qid: " + b)
  }else {
    if(a instanceof xc) {
      try {
        this.Yc(a.body, m)
      }catch(d) {
        this.ib("Peer's Notification caused uncaught exception", d)
      }
    }else {
      if(a instanceof sc) {
        if(b = a.ca, this.Za.Z(b)) {
          this.Bb("Received Question with duplicate qid: " + b)
        }else {
          a: {
            a = [a.body, j];
            try {
              c = this.Yc.apply(k, a ? a : [])
            }catch(g) {
              c = Nb(g);
              break a
            }
            c = c instanceof L ? c : c instanceof Error ? Nb(c) : Mb(c)
          }
          this.Za.set(b, c);
          var e = this;
          c.Y(function(a) {
            var c = b;
            e.Za.remove(c);
            e.da(new tc(a, c));
            return k
          }, function(a) {
            var c = b;
            e.Za.remove(c);
            a instanceof Dc ? e.da(new uc(a.body, c)) : a instanceof Fb ? e.da(new vc("CancelledError", c)) : (e.ib("Peer's Question #" + c + " caused uncaught exception", a), e.da(new vc("Uncaught exception", c)));
            return k
          });
          c.sb(function(a) {
            this.ib("Bug in QANHelper.sendOkayAnswer_ or sendErrorAnswer_", a);
            return k
          })
        }
      }else {
        a instanceof wc && (b = a.ca, c = this.Za.get(b), u(c) && c.cancel())
      }
    }
  }
};
p.me = function(a) {
  var b = this.Ob + 1;
  this.da(new sc(a, b));
  this.Ob += 1;
  var c = this, a = new L(function() {
    c.ma.set(b, k);
    c.da(new wc(b))
  });
  this.ma.set(b, a);
  return a
};
p.Te = function(a) {
  this.da(new xc(a))
};
p.md = function(a) {
  for(var b = this.ma.T(), c = 0;c < b.length;c++) {
    var d = this.ma.get(b[c]);
    u(d) && (this.ma.set(b[c], k), d.P(new Fc(a)))
  }
};
function Gc() {
  this.Ud = pa()
}
var Hc = new Gc;
Gc.prototype.set = aa("Ud");
Gc.prototype.reset = function() {
  this.set(pa())
};
Gc.prototype.get = o("Ud");
function Ic(a) {
  this.Ve = a || "";
  this.cf = Hc
}
Ic.prototype.be = j;
Ic.prototype.bf = j;
Ic.prototype.af = j;
Ic.prototype.ce = m;
function Jc(a) {
  return 10 > a ? "0" + a : "" + a
}
function Kc(a, b) {
  var c = (a.ee - b) / 1E3, d = c.toFixed(3), g = 0;
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
function Lc(a) {
  Ic.call(this, a)
}
A(Lc, Ic);
Lc.prototype.ce = j;
var Mc;
function Nc(a, b) {
  var c;
  c = a.className;
  c = v(c) && c.match(/\S+/g) || [];
  for(var d = kb(arguments, 1), g = c.length + d.length, e = c, h = 0;h < d.length;h++) {
    0 <= db(e, d[h]) || e.push(d[h])
  }
  a.className = c.join(" ");
  return c.length == g
}
;var Oc = !D || Ua();
!Ka && !D || D && Ua() || Ka && G("1.9.1");
D && G("9");
function Pc(a) {
  return a ? new Qc(9 == a.nodeType ? a : a.ownerDocument || a.document) : Mc || (Mc = new Qc)
}
function R(a) {
  return v(a) ? document.getElementById(a) : a
}
var Rc = {cellpadding:"cellPadding", cellspacing:"cellSpacing", colspan:"colSpan", rowspan:"rowSpan", valign:"vAlign", height:"height", width:"width", usemap:"useMap", frameborder:"frameBorder", maxlength:"maxLength", type:"type"};
function Sc(a, b, c) {
  return Tc(document, arguments)
}
function Tc(a, b) {
  var c = b[0], d = b[1];
  if(!Oc && d && (d.name || d.type)) {
    c = ["<", c];
    d.name && c.push(' name="', C(d.name), '"');
    if(d.type) {
      c.push(' type="', C(d.type), '"');
      var g = {};
      ab(g, d);
      d = g;
      delete d.type
    }
    c.push(">");
    c = c.join("")
  }
  var e = a.createElement(c);
  d && (v(d) ? e.className = d : fa(d) ? Nc.apply(k, [e].concat(d)) : Xa(d, function(a, b) {
    "style" == b ? e.style.cssText = a : "class" == b ? e.className = a : "for" == b ? e.htmlFor = a : b in Rc ? e.setAttribute(Rc[b], a) : 0 == b.lastIndexOf("aria-", 0) ? e.setAttribute(b, a) : e[b] = a
  }));
  2 < b.length && Uc(a, e, b, 2);
  return e
}
function Uc(a, b, c, d) {
  function g(c) {
    c && b.appendChild(v(c) ? a.createTextNode(c) : c)
  }
  for(;d < c.length;d++) {
    var e = c[d];
    if(ga(e) && !(ia(e) && 0 < e.nodeType)) {
      var h = eb, l;
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
      if(l) {
        if(l = e.length, 0 < l) {
          for(var n = Array(l), q = 0;q < l;q++) {
            n[q] = e[q]
          }
          e = n
        }else {
          e = []
        }
      }
      h(e, g)
    }else {
      g(e)
    }
  }
}
function Qc(a) {
  this.za = a || s.document || document
}
p = Qc.prototype;
p.pd = Pc;
p.Ba = function(a) {
  return v(a) ? this.za.getElementById(a) : a
};
function Vc(a, b) {
  var c;
  c = a.za;
  var d = b && "*" != b ? b.toUpperCase() : "";
  c = c.querySelectorAll && c.querySelector && d ? c.querySelectorAll(d + "") : c.getElementsByTagName(d || "*");
  return c
}
p.bb = function(a, b, c) {
  return Tc(this.za, arguments)
};
p.createElement = function(a) {
  return this.za.createElement(a)
};
p.createTextNode = function(a) {
  return this.za.createTextNode(a)
};
p.appendChild = function(a, b) {
  a.appendChild(b)
};
p.append = function(a, b) {
  Uc(9 == a.nodeType ? a : a.ownerDocument || a.document, a, arguments, 1)
};
p.contains = function(a, b) {
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
function Wc(a) {
  "number" == typeof a && (a = Math.round(a) + "px");
  return a
}
function Xc(a) {
  D ? a.cssText = ".dbg-sev{color:#F00}.dbg-w{color:#C40}.dbg-sh{font-weight:bold;color:#000}.dbg-i{color:#444}.dbg-f{color:#999}.dbg-ev{color:#0A0}.dbg-m{color:#990}.logmsg{border-bottom:1px solid #CCC;padding:2px}.logsep{background-color: #8C8;}.logdiv{border:1px solid #CCC;background-color:#FCFCFC;font:medium monospace}" : a[F ? "innerText" : "innerHTML"] = ".dbg-sev{color:#F00}.dbg-w{color:#C40}.dbg-sh{font-weight:bold;color:#000}.dbg-i{color:#444}.dbg-f{color:#999}.dbg-ev{color:#0A0}.dbg-m{color:#990}.logmsg{border-bottom:1px solid #CCC;padding:2px}.logsep{background-color: #8C8;}.logdiv{border:1px solid #CCC;background-color:#FCFCFC;font:medium monospace}"
}
;function Yc(a) {
  this.n = new O;
  a && this.$b(a)
}
function Zc(a) {
  var b = typeof a;
  return"object" == b && a || "function" == b ? "o" + ka(a) : b.substr(0, 1) + a
}
p = Yc.prototype;
p.A = function() {
  return this.n.A()
};
p.add = function(a) {
  this.n.set(Zc(a), a)
};
p.$b = function(a) {
  for(var a = ec(a), b = a.length, c = 0;c < b;c++) {
    this.add(a[c])
  }
};
p.Fc = function(a) {
  for(var a = ec(a), b = a.length, c = 0;c < b;c++) {
    this.remove(a[c])
  }
};
p.remove = function(a) {
  return this.n.remove(Zc(a))
};
p.clear = function() {
  this.n.clear()
};
p.fb = function() {
  return this.n.fb()
};
p.contains = function(a) {
  return this.n.Z(Zc(a))
};
p.C = function() {
  return this.n.C()
};
p.S = function() {
  return new Yc(this)
};
p.K = function(a) {
  var b;
  if(b = this.A() == dc(a)) {
    var c = a, a = dc(c);
    this.A() > a ? b = m : (!(c instanceof Yc) && 5 < a && (c = new Yc(c)), b = hc(this, function(a) {
      if("function" == typeof c.contains) {
        a = c.contains(a)
      }else {
        if("function" == typeof c.dc) {
          a = c.dc(a)
        }else {
          if(ga(c) || v(c)) {
            a = 0 <= db(c, a)
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
function $c(a) {
  return ad(a || arguments.callee.caller, [])
}
function ad(a, b) {
  var c = [];
  if(0 <= db(b, a)) {
    c.push("[...circular reference...]")
  }else {
    if(a && 50 > b.length) {
      c.push(bd(a) + "(");
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
            e = "" + e;
            break;
          case "boolean":
            e = e ? "true" : "false";
            break;
          case "function":
            e = (e = bd(e)) ? e : "[fn]";
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
        c.push(ad(a.caller, b))
      }catch(h) {
        c.push("[exception trying to get caller]\n")
      }
    }else {
      a ? c.push("[...long stack...]") : c.push("[end]")
    }
  }
  return c.join("")
}
function bd(a) {
  if(cd[a]) {
    return cd[a]
  }
  a = "" + a;
  if(!cd[a]) {
    var b = /function ([^\(]+)/.exec(a);
    cd[a] = b ? b[1] : "[Anonymous]"
  }
  return cd[a]
}
var cd = {};
function dd(a, b, c, d, g) {
  this.reset(a, b, c, d, g)
}
dd.prototype.lc = k;
dd.prototype.kc = k;
var ed = 0;
dd.prototype.reset = function(a, b, c, d, g) {
  "number" == typeof g || ed++;
  this.ee = d || pa();
  this.Ra = a;
  this.Jd = b;
  this.Pe = c;
  delete this.lc;
  delete this.kc
};
dd.prototype.Ic = aa("Ra");
function S(a) {
  this.Re = a
}
S.prototype.t = k;
S.prototype.Ra = k;
S.prototype.ia = k;
S.prototype.Na = k;
function T(a, b) {
  this.name = a;
  this.value = b
}
T.prototype.toString = o("name");
var fd = new T("OFF", Infinity), gd = new T("SHOUT", 1200), hd = new T("SEVERE", 1E3), id = new T("WARNING", 900), jd = new T("INFO", 800), kd = new T("CONFIG", 700), ld = new T("FINE", 500), md = new T("FINER", 400), nd = new T("FINEST", 300), od = new T("ALL", 0);
function U(a) {
  return V.rd(a)
}
p = S.prototype;
p.getParent = o("t");
p.Ic = aa("Ra");
function pd(a) {
  if(a.Ra) {
    return a.Ra
  }
  if(a.t) {
    return pd(a.t)
  }
  Aa("Root logger has no level set.");
  return k
}
p.log = function(a, b, c) {
  if(a.value >= pd(this).value) {
    a = this.He(a, b, c);
    b = "log:" + a.Jd;
    s.console && (s.console.timeStamp ? s.console.timeStamp(b) : s.console.markTimeline && s.console.markTimeline(b));
    s.msWriteProfilerMark && s.msWriteProfilerMark(b);
    for(b = this;b;) {
      var c = b, d = a;
      if(c.Na) {
        for(var g = 0, e = i;e = c.Na[g];g++) {
          e(d)
        }
      }
      b = b.getParent()
    }
  }
};
p.He = function(a, b, c) {
  var d = new dd(a, "" + b, this.Re);
  if(c) {
    d.lc = c;
    var g;
    var e = arguments.callee.caller;
    try {
      var h;
      var l = da("window.location.href");
      if(v(c)) {
        h = {message:c, name:"Unknown error", lineNumber:"Not available", fileName:l, stack:"Not available"}
      }else {
        var n, q, z = m;
        try {
          n = c.lineNumber || c.Oe || "Not available"
        }catch(r) {
          n = "Not available", z = j
        }
        try {
          q = c.fileName || c.filename || c.sourceURL || l
        }catch(w) {
          q = "Not available", z = j
        }
        h = z || !c.lineNumber || !c.fileName || !c.stack ? {message:c.message, name:c.name, lineNumber:n, fileName:q, stack:c.stack || "Not available"} : c
      }
      g = "Message: " + C(h.message) + '\nUrl: <a href="view-source:' + h.fileName + '" target="_new">' + h.fileName + "</a>\nLine: " + h.lineNumber + "\n\nBrowser stack:\n" + C(h.stack + "-> ") + "[end]\n\nJS stack traversal:\n" + C($c(e) + "-> ")
    }catch(E) {
      g = "Exception trying to expose exception! You win, we lose. " + E
    }
    d.kc = g
  }
  return d
};
p.$e = function(a, b) {
  this.log(gd, a, b)
};
p.H = function(a, b) {
  this.log(hd, a, b)
};
p.q = function(a, b) {
  this.log(id, a, b)
};
p.info = function(a, b) {
  this.log(jd, a, b)
};
p.ue = function(a, b) {
  this.log(kd, a, b)
};
p.j = function(a, b) {
  this.log(ld, a, b)
};
p.De = function(a, b) {
  this.log(md, a, b)
};
p.s = function(a, b) {
  this.log(nd, a, b)
};
var V = {Kb:{}, mb:k, xd:function() {
  V.mb || (V.mb = new S(""), V.Kb[""] = V.mb, V.mb.Ic(kd))
}, vg:function() {
  return V.Kb
}, nc:function() {
  V.xd();
  return V.mb
}, rd:function(a) {
  V.xd();
  return V.Kb[a] || V.we(a)
}, ug:function(a) {
  return function(b) {
    (a || V.nc()).H("Error: " + b.message + " (" + b.fileName + " @ Line: " + b.Oe + ")")
  }
}, we:function(a) {
  var b = new S(a), c = a.lastIndexOf("."), d = a.substr(c + 1), c = V.rd(a.substr(0, c));
  c.ia || (c.ia = {});
  c.ia[d] = b;
  b.t = c;
  return V.Kb[a] = b
}};
function qd(a) {
  this.Sd = x(this.ke, this);
  this.od = new Lc;
  this.zd = this.od.be = m;
  this.h = a;
  this.Be = this.h.ownerDocument || this.h.document;
  var a = Pc(this.h), b = k;
  if(D) {
    b = a.za.createStyleSheet(), Xc(b)
  }else {
    var c = Vc(a, "head")[0];
    c || (b = Vc(a, "body")[0], c = a.bb("head"), b.parentNode.insertBefore(c, b));
    b = a.bb("style");
    Xc(b);
    a.appendChild(c, b)
  }
  this.h.className += " logdiv"
}
qd.prototype.Ze = function(a) {
  if(a != this.zd) {
    var b = V.nc();
    if(a) {
      var c = this.Sd;
      b.Na || (b.Na = []);
      b.Na.push(c)
    }else {
      (b = b.Na) && ib(b, this.Sd)
    }
    this.zd = a
  }
};
qd.prototype.ke = function(a) {
  var b = 100 >= this.h.scrollHeight - this.h.scrollTop - this.h.clientHeight, c = this.Be.createElement("div");
  c.className = "logmsg";
  var d = this.od, g;
  switch(a.Ra.value) {
    case gd.value:
      g = "dbg-sh";
      break;
    case hd.value:
      g = "dbg-sev";
      break;
    case id.value:
      g = "dbg-w";
      break;
    case jd.value:
      g = "dbg-i";
      break;
    default:
      g = "dbg-f"
  }
  var e = [];
  e.push(d.Ve, " ");
  if(d.be) {
    var h = new Date(a.ee);
    e.push("[", Jc(h.getFullYear() - 2E3) + Jc(h.getMonth() + 1) + Jc(h.getDate()) + " " + Jc(h.getHours()) + ":" + Jc(h.getMinutes()) + ":" + Jc(h.getSeconds()) + "." + Jc(Math.floor(h.getMilliseconds() / 10)), "] ")
  }
  d.bf && e.push("[", xa(Kc(a, d.cf.get())), "s] ");
  d.af && e.push("[", C(a.Pe), "] ");
  e.push('<span class="', g, '">', ra(xa(C(a.Jd))));
  d.ce && a.lc && e.push("<br>", ra(xa(a.kc || "")));
  e.push("</span><br>");
  c.innerHTML = e.join("");
  this.h.appendChild(c);
  b && (this.h.scrollTop = this.h.scrollHeight)
};
qd.prototype.clear = function() {
  this.h.innerHTML = ""
};
var rd = RegExp("^(?:([^:/?#.]+):)?(?://(?:([^/?#]*)@)?([\\w\\d\\-\\u0100-\\uffff.%]*)(?::([0-9]+))?)?([^?#]+)?(?:\\?([^#]*))?(?:#(.*))?$");
function sd(a, b) {
  var c = a.match(rd), d = b.match(rd);
  return c[3] == d[3] && c[1] == d[1] && c[4] == d[4]
}
;function td(a, b) {
  var c;
  if(a instanceof td) {
    this.L = u(b) ? b : a.L, ud(this, a.ta), c = a.Ja, W(this), this.Ja = c, wd(this, a.ka), xd(this, a.Ua), yd(this, a.na), zd(this, a.Q.S()), c = a.Aa, W(this), this.Aa = c
  }else {
    if(a && (c = ("" + a).match(rd))) {
      this.L = !!b;
      ud(this, c[1] || "", j);
      var d = c[2] || "";
      W(this);
      this.Ja = d ? decodeURIComponent(d) : "";
      wd(this, c[3] || "", j);
      xd(this, c[4]);
      yd(this, c[5] || "", j);
      zd(this, c[6] || "", j);
      c = c[7] || "";
      W(this);
      this.Aa = c ? decodeURIComponent(c) : ""
    }else {
      this.L = !!b, this.Q = new Ad(k, 0, this.L)
    }
  }
}
p = td.prototype;
p.ta = "";
p.Ja = "";
p.ka = "";
p.Ua = k;
p.na = "";
p.Aa = "";
p.Ne = m;
p.L = m;
p.toString = function() {
  var a = [], b = this.ta;
  b && a.push(Bd(b, Cd), ":");
  if(b = this.ka) {
    a.push("//");
    var c = this.Ja;
    c && a.push(Bd(c, Cd), "@");
    a.push(encodeURIComponent("" + b));
    b = this.Ua;
    b != k && a.push(":", "" + b)
  }
  if(b = this.na) {
    this.ka && "/" != b.charAt(0) && a.push("/"), a.push(Bd(b, "/" == b.charAt(0) ? Dd : Ed))
  }
  (b = this.Q.toString()) && a.push("?", b);
  (b = this.Aa) && a.push("#", Bd(b, Fd));
  return a.join("")
};
p.S = function() {
  return new td(this)
};
function ud(a, b, c) {
  W(a);
  a.ta = c ? b ? decodeURIComponent(b) : "" : b;
  a.ta && (a.ta = a.ta.replace(/:$/, ""))
}
function wd(a, b, c) {
  W(a);
  a.ka = c ? b ? decodeURIComponent(b) : "" : b
}
function xd(a, b) {
  W(a);
  b ? (b = Number(b), (isNaN(b) || 0 > b) && f(Error("Bad port number " + b)), a.Ua = b) : a.Ua = k
}
function yd(a, b, c) {
  W(a);
  a.na = c ? b ? decodeURIComponent(b) : "" : b
}
function zd(a, b, c) {
  W(a);
  b instanceof Ad ? (a.Q = b, a.Q.Hc(a.L)) : (c || (b = Bd(b, Gd)), a.Q = new Ad(b, 0, a.L))
}
function W(a) {
  a.Ne && f(Error("Tried to modify a read-only Uri"))
}
p.Hc = function(a) {
  this.L = a;
  this.Q && this.Q.Hc(a);
  return this
};
function Hd(a) {
  return a instanceof td ? a.S() : new td(a, i)
}
function Bd(a, b) {
  return v(a) ? encodeURI(a).replace(b, Id) : k
}
function Id(a) {
  a = a.charCodeAt(0);
  return"%" + (a >> 4 & 15).toString(16) + (a & 15).toString(16)
}
var Cd = /[#\/\?@]/g, Ed = /[\#\?:]/g, Dd = /[\#\?]/g, Gd = /[\#\?@]/g, Fd = /#/g;
function Ad(a, b, c) {
  this.F = a || k;
  this.L = !!c
}
function Jd(a) {
  if(!a.l && (a.l = new O, a.c = 0, a.F)) {
    for(var b = a.F.split("&"), c = 0;c < b.length;c++) {
      var d = b[c].indexOf("="), g = k, e = k;
      0 <= d ? (g = b[c].substring(0, d), e = b[c].substring(d + 1)) : g = b[c];
      g = decodeURIComponent(g.replace(/\+/g, " "));
      g = Kd(a, g);
      a.add(g, e ? decodeURIComponent(e.replace(/\+/g, " ")) : "")
    }
  }
}
p = Ad.prototype;
p.l = k;
p.c = k;
p.A = function() {
  Jd(this);
  return this.c
};
p.add = function(a, b) {
  Jd(this);
  this.F = k;
  var a = Kd(this, a), c = this.l.get(a);
  c || this.l.set(a, c = []);
  c.push(b);
  this.c++;
  return this
};
p.remove = function(a) {
  Jd(this);
  a = Kd(this, a);
  return this.l.Z(a) ? (this.F = k, this.c -= this.l.get(a).length, this.l.remove(a)) : m
};
p.clear = function() {
  this.l = this.F = k;
  this.c = 0
};
p.fb = function() {
  Jd(this);
  return 0 == this.c
};
p.Z = function(a) {
  Jd(this);
  a = Kd(this, a);
  return this.l.Z(a)
};
p.dc = function(a) {
  var b = this.C();
  return 0 <= db(b, a)
};
p.T = function() {
  Jd(this);
  for(var a = this.l.C(), b = this.l.T(), c = [], d = 0;d < b.length;d++) {
    for(var g = a[d], e = 0;e < g.length;e++) {
      c.push(b[d])
    }
  }
  return c
};
p.C = function(a) {
  Jd(this);
  var b = [];
  if(a) {
    this.Z(a) && (b = jb(b, this.l.get(Kd(this, a))))
  }else {
    for(var a = this.l.C(), c = 0;c < a.length;c++) {
      b = jb(b, a[c])
    }
  }
  return b
};
p.set = function(a, b) {
  Jd(this);
  this.F = k;
  a = Kd(this, a);
  this.Z(a) && (this.c -= this.l.get(a).length);
  this.l.set(a, [b]);
  this.c++;
  return this
};
p.get = function(a, b) {
  var c = a ? this.C(a) : [];
  return 0 < c.length ? c[0] : b
};
p.toString = function() {
  if(this.F) {
    return this.F
  }
  if(!this.l) {
    return""
  }
  for(var a = [], b = this.l.T(), c = 0;c < b.length;c++) {
    for(var d = b[c], g = encodeURIComponent("" + d), d = this.C(d), e = 0;e < d.length;e++) {
      var h = g;
      "" !== d[e] && (h += "=" + encodeURIComponent("" + d[e]));
      a.push(h)
    }
  }
  return this.F = a.join("&")
};
p.S = function() {
  var a = new Ad;
  a.F = this.F;
  this.l && (a.l = this.l.S());
  return a
};
function Kd(a, b) {
  var c = "" + b;
  a.L && (c = c.toLowerCase());
  return c
}
p.Hc = function(a) {
  a && !this.L && (Jd(this), this.F = k, gc(this.l, function(a, c) {
    var d = c.toLowerCase();
    c != d && (this.remove(c), this.remove(d), 0 < a.length && (this.F = k, this.l.set(Kd(this, d), a), this.c += a.length))
  }, this));
  this.L = a
};
function Ld(a) {
  var b = t(a);
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
;function Md(a, b) {
  this.Ka = a;
  this.Ga = b
}
Md.prototype.K = function(a) {
  return a instanceof Md && this.Ka == a.Ka && this.Ga.join(",") == a.Ga
};
Md.prototype.v = function(a, b) {
  a.push("new SACK(", "" + this.Ka, ", ");
  M(this.Ga, a, b);
  a.push(")")
};
function Nd() {
  this.G = new O
}
Nd.prototype.ya = -1;
Nd.prototype.I = 0;
Nd.prototype.append = function(a) {
  var b = Ld(a);
  this.G.set(this.ya + 1, [a, b]);
  this.ya += 1;
  this.I += b
};
Nd.prototype.v = function(a) {
  a.push("<Queue with ", "" + this.G.A(), " item(s), counter=#", "" + this.ya, ", size=", "" + this.I, ">")
};
function Od(a) {
  a = a.G.T();
  H.sort.call(a, lb);
  return a
}
function Pd() {
  this.wa = new O
}
Pd.prototype.Ea = -1;
Pd.prototype.I = 0;
function Qd(a) {
  var b = a.wa.T();
  H.sort.call(b, lb);
  return new Md(a.Ea, b)
}
var Rd = {};
function Sd(a, b) {
  switch(t(b)) {
    case "string":
      a.push("<string>", C(b), "</string>");
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
        a.push('<property id="', d, '">'), Sd(a, b[d]), a.push("</property>")
      }
      a.push("</array>");
      break;
    case "object":
      if("function" == typeof b.getFullYear) {
        a.push("<date>", b.valueOf(), "</date>")
      }else {
        a.push("<object>");
        for(c in b) {
          Object.prototype.hasOwnProperty.call(b, c) && "function" != t(b[c]) && (a.push('<property id="', C(c), '">'), Sd(a, b[c]), a.push("</property>"))
        }
        a.push("</object>")
      }
      break;
    default:
      a.push("<null/>")
  }
}
function Td(a, b) {
  var c = ['<invoke name="', a, '" returntype="javascript">'], d = c, g = arguments;
  d.push("<arguments>");
  for(var e = g.length, h = 1;h < e;h++) {
    Sd(d, g[h])
  }
  d.push("</arguments>");
  c.push("</invoke>");
  return c.join("")
}
;var Ud = m, Vd = "";
function Wd(a) {
  a = a.match(/[\d]+/g);
  a.length = 3;
  return a.join(".")
}
if(navigator.plugins && navigator.plugins.length) {
  var Xd = navigator.plugins["Shockwave Flash"];
  Xd && (Ud = j, Xd.description && (Vd = Wd(Xd.description)));
  navigator.plugins["Shockwave Flash 2.0"] && (Ud = j, Vd = "2.0.0.11")
}else {
  if(navigator.mimeTypes && navigator.mimeTypes.length) {
    var Yd = navigator.mimeTypes["application/x-shockwave-flash"];
    (Ud = Yd && Yd.enabledPlugin) && (Vd = Wd(Yd.enabledPlugin.description))
  }else {
    try {
      var Zd = new ActiveXObject("ShockwaveFlash.ShockwaveFlash.7"), Ud = j, Vd = Wd(Zd.GetVariable("$version"))
    }catch($d) {
      try {
        Zd = new ActiveXObject("ShockwaveFlash.ShockwaveFlash.6"), Ud = j, Vd = "6.0.21"
      }catch(ae) {
        try {
          Zd = new ActiveXObject("ShockwaveFlash.ShockwaveFlash"), Ud = j, Vd = Wd(Zd.GetVariable("$version"))
        }catch(be) {
        }
      }
    }
  }
}
var ce = Vd;
function de(a) {
  this.Je = a;
  this.g = []
}
A(de, I);
var ee = [];
de.prototype.Fc = function() {
  eb(this.g, yb);
  this.g.length = 0
};
de.prototype.d = function() {
  de.m.d.call(this);
  this.Fc()
};
de.prototype.handleEvent = function() {
  f(Error("EventHandler.handleEvent not implemented"))
};
function fe() {
}
fe.qd = function() {
  return fe.yd ? fe.yd : fe.yd = new fe
};
fe.prototype.Se = 0;
fe.qd();
function ge(a) {
  this.xb = a || Pc()
}
A(ge, Db);
p = ge.prototype;
p.Me = fe.qd();
p.U = k;
p.Da = m;
p.h = k;
p.t = k;
p.ia = k;
p.wb = k;
p.of = m;
function he(a) {
  return a.U || (a.U = ":" + (a.Me.Se++).toString(36))
}
p.Ba = o("h");
p.getParent = o("t");
p.Jc = function(a) {
  this.t && this.t != a && f(Error("Method not supported"));
  ge.m.Jc.call(this, a)
};
p.pd = o("xb");
p.bb = function() {
  this.h = this.xb.createElement("div")
};
p.yb = function() {
  this.Da = j;
  ie(this, function(a) {
    !a.Da && a.Ba() && a.yb()
  })
};
function je(a) {
  ie(a, function(a) {
    a.Da && je(a)
  });
  a.Fb && a.Fb.Fc();
  a.Da = m
}
p.d = function() {
  ge.m.d.call(this);
  this.Da && je(this);
  this.Fb && (this.Fb.b(), delete this.Fb);
  ie(this, function(a) {
    a.b()
  });
  if(!this.of && this.h) {
    var a = this.h;
    a && a.parentNode && a.parentNode.removeChild(a)
  }
  this.t = this.h = this.wb = this.ia = k
};
function ie(a, b) {
  a.ia && eb(a.ia, b, i)
}
p.removeChild = function(a, b) {
  if(a) {
    var c = v(a) ? a : he(a), d;
    this.wb && c ? (d = this.wb, d = (c in d ? d[c] : i) || k) : d = k;
    a = d;
    c && a && (d = this.wb, c in d && delete d[c], ib(this.ia, a), b && (je(a), a.h && (c = a.h) && c.parentNode && c.parentNode.removeChild(c)), c = a, c == k && f(Error("Unable to set parent component")), c.t = k, ge.m.Jc.call(c, k))
  }
  a || f(Error("Child is not in parent component"));
  return a
};
function ke(a, b) {
  this.xb = b || Pc();
  this.Fe = a;
  this.jc = new de(this);
  this.Cb = new O
}
A(ke, ge);
p = ke.prototype;
p.a = U("goog.ui.media.FlashObject");
p.qf = "window";
p.Xc = "#000000";
p.le = "sameDomain";
function le(a, b, c) {
  a.Uc = v(b) ? b : Math.round(b) + "px";
  a.pc = v(c) ? c : Math.round(c) + "px";
  a.Ba() && (b = a.Ba() ? a.Ba().firstChild : k, c = a.Uc, a = a.pc, a == i && f(Error("missing height argument")), b.style.width = Wc(c), b.style.height = Wc(a))
}
p.yb = function() {
  ke.m.yb.call(this);
  var a = this.Ba(), b;
  b = D ? '<object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000" id="%s" name="%s" class="%s"><param name="movie" value="%s"/><param name="quality" value="high"/><param name="FlashVars" value="%s"/><param name="bgcolor" value="%s"/><param name="AllowScriptAccess" value="%s"/><param name="allowFullScreen" value="true"/><param name="SeamlessTabbing" value="false"/>%s</object>' : '<embed quality="high" id="%s" name="%s" class="%s" src="%s" FlashVars="%s" bgcolor="%s" AllowScriptAccess="%s" allowFullScreen="true" SeamlessTabbing="false" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/go/getflashplayer" %s></embed>';
  for(var c = D ? '<param name="wmode" value="%s"/>' : "wmode=%s", c = qa(c, this.qf), d = this.Cb.T(), g = this.Cb.C(), e = [], h = 0;h < d.length;h++) {
    e.push(encodeURIComponent("" + d[h]) + "=" + encodeURIComponent("" + g[h]))
  }
  b = qa(b, he(this), he(this), "goog-ui-media-flash-object", C(this.Fe), C(e.join("&")), this.Xc, this.le, c);
  a.innerHTML = b;
  this.Uc && this.pc && le(this, this.Uc, this.pc);
  a = this.jc;
  b = this.Ba();
  c = Ya(mb);
  fa(c) || (ee[0] = c, c = ee);
  for(d = 0;d < c.length;d++) {
    a.g.push(ub(b, c[d], pb || a, m, a.Je || a))
  }
};
p.bb = function() {
  this.Wd != k && !(0 <= ya(ce, this.Wd)) && (this.a.q("Required flash version not found:" + this.Wd), f(Error("Method not supported")));
  var a = this.pd().createElement("div");
  a.className = "goog-ui-media-flash";
  this.h = a
};
p.d = function() {
  ke.m.d.call(this);
  this.Cb = k;
  this.jc.b();
  this.jc = k
};
function me(a) {
  B.call(this, a)
}
A(me, B);
me.prototype.name = "cw.loadflash.FlashLoadFailed";
s.__loadFlashObject_callbacks = {};
function ne(a, b) {
  this.U = "_" + Yb();
  this.Wb = a;
  this.pa = b;
  this.va = a.va
}
A(ne, I);
p = ne.prototype;
p.Sa = j;
p.fc = m;
p.a = U("cw.net.FlashSocket");
p.v = function(a) {
  a.push("<FlashSocket id='");
  a.push(this.U);
  a.push("'>")
};
function oe(a, b, c) {
  if("frames" == b) {
    a = a.pa, pe(a.w), qe(a.w, c)
  }else {
    if("stillreceiving" == b) {
      c = a.pa, c.a.s("onstillreceiving"), pe(c.w)
    }else {
      if("connect" == b) {
        a.pa.onconnect()
      }else {
        "close" == b ? (a.Sa = m, a.b()) : "ioerror" == b ? (a.Sa = m, b = a.pa, b.a.q("onioerror: " + N(c)), re(b.w, m), a.b()) : "securityerror" == b ? (a.Sa = m, b = a.pa, b.a.q("onsecurityerror: " + N(c)), re(b.w, m), a.b()) : f(Error("bad event: " + b))
      }
    }
  }
}
function se(a) {
  a.fc = j;
  a.Sa = m;
  a.b()
}
p.cc = function(a, b) {
  try {
    var c = this.va.CallFunction(Td("__FC_connect", this.U, a, b, "<int32/>\n"))
  }catch(d) {
    return this.a.H("connect: could not call __FC_connect; Flash probably crashed. Disposing now. Error was: " + d.message), se(this)
  }
  '"OK"' != c && f(Error("__FC_connect failed? ret: " + c))
};
p.rb = function(a) {
  try {
    var b = this.va.CallFunction(Td("__FC_writeFrames", this.U, a))
  }catch(c) {
    return this.a.H("writeFrames: could not call __FC_writeFrames; Flash probably crashed. Disposing now. Error was: " + c.message), se(this)
  }
  '"OK"' != b && ('"no such instance"' == b ? (this.a.q("Flash no longer knows of " + this.U + "; disposing."), this.b()) : f(Error("__FC_writeFrames failed? ret: " + b)))
};
p.d = function() {
  this.a.info("in disposeInternal, needToCallClose_=" + this.Sa);
  ne.m.d.call(this);
  var a = this.va;
  delete this.va;
  if(this.Sa) {
    try {
      this.a.info("disposeInternal: __FC_close ret: " + a.CallFunction(Td("__FC_close", this.U)))
    }catch(b) {
      this.a.H("disposeInternal: could not call __FC_close; Flash probably crashed. Error was: " + b.message), this.fc = j
    }
  }
  if(this.fc) {
    a = this.pa, a.a.q("oncrash"), re(a.w, j)
  }else {
    this.pa.onclose()
  }
  delete this.pa;
  delete this.Wb.Oa[this.U]
};
function te(a, b) {
  this.o = a;
  this.va = b;
  this.Oa = {};
  this.bc = "__FST_" + Yb();
  s[this.bc] = x(this.Ae, this);
  var c = b.CallFunction(Td("__FC_setCallbackFunc", this.bc));
  '"OK"' != c && f(Error("__FC_setCallbackFunc failed? ret: " + c))
}
A(te, I);
p = te.prototype;
p.a = U("cw.net.FlashSocketTracker");
p.v = function(a, b) {
  a.push("<FlashSocketTracker instances=");
  M(this.Oa, a, b);
  a.push(">")
};
p.gc = function(a) {
  a = new ne(this, a);
  return this.Oa[a.U] = a
};
p.ye = function(a, b, c, d) {
  var g = this.Oa[a];
  g ? "frames" == b && d ? (oe(g, "ioerror", "FlashConnector hadError while handling data."), g.b()) : oe(g, b, c) : this.a.q("Cannot dispatch because we have no instance: " + N([a, b, c, d]))
};
p.Ae = function(a, b, c, d) {
  try {
    var g = this.o;
    g.zb.push([this.ye, this, [a, b, c, d]]);
    g.Qc == k && (g.Qc = g.z.setTimeout(g.re, 0))
  }catch(e) {
    s.window.setTimeout(function() {
      f(e)
    }, 0)
  }
};
p.d = function() {
  te.m.d.call(this);
  for(var a = Ya(this.Oa);a.length;) {
    a.pop().b()
  }
  delete this.Oa;
  delete this.va;
  s[this.bc] = i
};
function ue(a) {
  this.w = a;
  this.ab = []
}
A(ue, I);
p = ue.prototype;
p.a = U("cw.net.FlashSocketConduit");
p.rb = function(a) {
  this.ab ? (this.a.s("writeFrames: Not connected, can't write " + a.length + " frame(s) yet."), this.ab.push.apply(this.ab, a)) : (this.a.s("writeFrames: Writing " + a.length + " frame(s)."), this.Tb.rb(a))
};
p.cc = function(a, b) {
  this.Tb.cc(a, b)
};
p.onconnect = function() {
  this.a.info("onconnect");
  pe(this.w);
  var a = this.ab;
  this.ab = k;
  a.length && (this.a.s("onconnect: Writing " + a.length + " buffered frame(s)."), this.Tb.rb(a))
};
p.onclose = function() {
  this.a.info("onclose");
  re(this.w, m)
};
p.d = function() {
  this.a.info("in disposeInternal.");
  ue.m.d.call(this);
  this.Tb.b();
  delete this.w
};
var ve = [];
function we() {
  var a = new L;
  ve.push(a);
  return a
}
function xe(a) {
  var b = ve;
  ve = [];
  eb(b, function(b) {
    b.N(a)
  });
  return k
}
function ye(a) {
  var b = ve;
  ve = [];
  eb(b, function(b) {
    b.P(a)
  });
  return k
}
;function ze() {
  var a = Math.pow(10, 9);
  return a + Math.random() * (Math.pow(10, 10) - a)
}
;function X(a) {
  B.call(this, a)
}
A(X, B);
X.prototype.name = "cw.net.InvalidFrame";
function Y() {
  var a = [];
  this.O(a);
  return a.join("")
}
function Ae() {
}
Ae.prototype.K = function(a, b) {
  return!(a instanceof Ae) ? m : pc(Be(this), Be(a), b)
};
Ae.prototype.v = function(a, b) {
  a.push("<HelloFrame properties=");
  M(Be(this), a, b);
  a.push(">")
};
function Be(a) {
  return[a.fa, a.Qd, a.wd, a.Vd, a.ob, a.Nc, a.Kd, a.Id, a.xc, a.Gd, a.ge, a.de, a.sa, a.Ib]
}
Ae.prototype.J = Y;
Ae.prototype.O = function(a) {
  var b = {};
  b.tnum = this.fa;
  b.ver = this.Qd;
  b.format = this.wd;
  b["new"] = this.Vd;
  b.id = this.ob;
  b.ming = this.Nc;
  b.pad = this.Kd;
  b.maxb = this.Id;
  u(this.xc) && (b.maxt = this.xc);
  b.maxia = this.Gd;
  b.tcpack = this.ge;
  b.eeds = this.de;
  b.sack = this.sa instanceof Md ? Zb((new Ce(this.sa)).J()) : this.sa;
  b.seenack = this.Ib instanceof Md ? Zb((new Ce(this.Ib)).J()) : this.Ib;
  for(var c in b) {
    b[c] === i && delete b[c]
  }
  a.push(Rb(b), "H")
};
function De(a) {
  P.call(this, "StringFrame", [a]);
  this.Pc = a
}
A(De, P);
De.prototype.J = Y;
De.prototype.O = function(a) {
  a.push(this.Pc, " ")
};
function Ee(a) {
  P.call(this, "CommentFrame", [a]);
  this.te = a
}
A(Ee, P);
Ee.prototype.J = Y;
Ee.prototype.O = function(a) {
  a.push(this.te, "^")
};
function Fe(a) {
  P.call(this, "SeqNumFrame", [a]);
  this.ae = a
}
A(Fe, P);
Fe.prototype.J = Y;
Fe.prototype.O = function(a) {
  a.push("" + this.ae, "N")
};
function Ge(a) {
  var b = a.split("|");
  if(2 != b.length) {
    return k
  }
  a: {
    var c = b[1], a = cc;
    if(ac.test(c) && (c = parseInt(c, 10), -1 <= c && c <= a)) {
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
      var e = bc(b[d]);
      if(e == k) {
        return k
      }
      c.push(e)
    }
  }
  return new Md(a, c)
}
function Ce(a) {
  P.call(this, "SackFrame", [a]);
  this.sa = a
}
A(Ce, P);
Ce.prototype.J = Y;
Ce.prototype.O = function(a) {
  var b = this.sa;
  a.push(b.Ga.join(","), "|", "" + b.Ka);
  a.push("A")
};
function He(a) {
  P.call(this, "StreamStatusFrame", [a]);
  this.Cd = a
}
A(He, P);
He.prototype.J = Y;
He.prototype.O = function(a) {
  var b = this.Cd;
  a.push(b.Ga.join(","), "|", "" + b.Ka);
  a.push("T")
};
function Ie() {
  P.call(this, "StreamCreatedFrame", [])
}
A(Ie, P);
Ie.prototype.J = Y;
Ie.prototype.O = function(a) {
  a.push("C")
};
function Je() {
  P.call(this, "YouCloseItFrame", [])
}
A(Je, P);
Je.prototype.J = Y;
Je.prototype.O = function(a) {
  a.push("Y")
};
function Ke(a, b) {
  P.call(this, "ResetFrame", [a, b]);
  this.Td = a;
  this.Wc = b
}
A(Ke, P);
Ke.prototype.J = Y;
Ke.prototype.O = function(a) {
  a.push(this.Td, "|", "" + Number(this.Wc), "!")
};
var Ne = {stream_attach_failure:"stream_attach_failure", acked_unsent_strings:"acked_unsent_strings", invalid_frame_type_or_arguments:"invalid_frame_type_or_arguments", frame_corruption:"frame_corruption", rwin_overflow:"rwin_overflow"};
function Oe(a) {
  P.call(this, "TransportKillFrame", [a]);
  this.reason = a
}
A(Oe, P);
Oe.prototype.J = Y;
Oe.prototype.O = function(a) {
  a.push(this.reason, "K")
};
function Pe(a) {
  a || f(new X("0-length frame"));
  var b = a.substr(a.length - 1, 1);
  if(" " == b) {
    return new De(a.substr(0, a.length - 1))
  }
  if("A" == b) {
    return a = Ge(Zb(a)), a == k && f(new X("bad sack")), new Ce(a)
  }
  if("N" == b) {
    return a = bc(Zb(a)), a == k && f(new X("bad seqNum")), new Fe(a)
  }
  if("T" == b) {
    return a = Ge(Zb(a)), a == k && f(new X("bad lastSackSeen")), new He(a)
  }
  if("Y" == b) {
    return 1 != a.length && f(new X("leading garbage")), new Je
  }
  if("^" == b) {
    return new Ee(a.substr(0, a.length - 1))
  }
  if("C" == b) {
    return 1 != a.length && f(new X("leading garbage")), new Ie
  }
  if("!" == b) {
    return b = a.substr(0, a.length - 3), (255 < b.length || !/^([ -~]*)$/.test(b)) && f(new X("bad reasonString")), a = {"|0":m, "|1":j}[a.substr(a.length - 3, 2)], a == k && f(new X("bad applicationLevel")), new Ke(b, a)
  }
  if("K" == b) {
    return a = a.substr(0, a.length - 1), a = Ne[a], a == k && f(new X("unknown kill reason: " + a)), new Oe(a)
  }
  f(new X("Invalid frame type " + b))
}
;function Qe(a, b, c, d) {
  this.contentWindow = a;
  this.Ab = b;
  this.Oc = c;
  this.Ge = d
}
Qe.prototype.v = function(a, b) {
  a.push("<XDRFrame frameId=");
  M(this.Ge, a, b);
  a.push(", expandedUrl=");
  M(this.Ab, a, b);
  a.push(", streams=");
  M(this.Oc, a, b);
  a.push(">")
};
function Re() {
  this.frames = [];
  this.vc = new O
}
Re.prototype.a = U("cw.net.XDRTracker");
function Se(a, b) {
  for(var c = Te, d = 0;d < c.frames.length;d++) {
    var g = c.frames[d], e;
    if(e = 0 == g.Oc.length) {
      e = g.Ab;
      var h = ("" + a).replace(/([-()\[\]{}+?*.$\^|,:#<!\\])/g, "\\$1").replace(/\x08/g, "\\x08").replace(/%random%/g, "ml" + Array(21).join("\\d"));
      e = RegExp("^" + h + "$").test(e)
    }
    if(e) {
      return c.a.info("Giving " + N(b) + " existing frame " + N(g)), Mb(g)
    }
  }
  d = Yb() + Yb();
  g = a.replace(/%random%/g, function() {
    return"ml" + Math.floor(ze()) + ("" + Math.floor(ze()))
  });
  e = s.location;
  e instanceof td || (e = Hd(e));
  g instanceof td || (g = Hd(g));
  var l = e;
  e = g;
  g = l.S();
  (h = !!e.ta) ? ud(g, e.ta) : h = !!e.Ja;
  if(h) {
    var n = e.Ja;
    W(g);
    g.Ja = n
  }else {
    h = !!e.ka
  }
  h ? wd(g, e.ka) : h = e.Ua != k;
  n = e.na;
  if(h) {
    xd(g, e.Ua)
  }else {
    if(h = !!e.na) {
      if("/" != n.charAt(0) && (l.ka && !l.na ? n = "/" + n : (l = g.na.lastIndexOf("/"), -1 != l && (n = g.na.substr(0, l + 1) + n))), ".." == n || "." == n) {
        n = ""
      }else {
        if(!(-1 == n.indexOf("./") && -1 == n.indexOf("/."))) {
          for(var l = 0 == n.lastIndexOf("/", 0), n = n.split("/"), q = [], z = 0;z < n.length;) {
            var r = n[z++];
            "." == r ? l && z == n.length && q.push("") : ".." == r ? ((1 < q.length || 1 == q.length && "" != q[0]) && q.pop(), l && z == n.length && q.push("")) : (q.push(r), l = j)
          }
          n = q.join("/")
        }
      }
    }
  }
  h ? yd(g, n) : h = "" !== e.Q.toString();
  h ? zd(g, e.Q.toString() ? decodeURIComponent(e.Q.toString()) : "") : h = !!e.Aa;
  h && (e = e.Aa, W(g), g.Aa = e);
  g = g.toString();
  e = ("" + s.location).match(rd)[3] || k;
  h = g.match(rd)[3] || k;
  e == h ? (c.a.info("No need to make a real XDRFrame for " + N(b)), c = Mb(new Qe(s, g, [b], k))) : ((e = R("minerva-elements")) || f(Error('makeWindowForUrl_: Page is missing an empty div with id "minerva-elements"; please add one.')), h = new L, c.vc.set(d, [h, g, b]), c.a.info("Creating new XDRFrame " + N(d) + "for " + N(b)), c = Sc("iframe", {id:"minerva-xdrframe-" + d, style:"visibility: hidden; height: 0; width: 0; border: 0; margin: 0;", src:g + "xdrframe/?domain=" + document.domain + "&id=" + 
  d}), e.appendChild(c), c = h);
  return c
}
Re.prototype.sf = function(a) {
  var b = this.vc.get(a);
  b || f(Error("Unknown frameId " + N(a)));
  this.vc.remove(b);
  var c = b[0], a = new Qe(R("minerva-xdrframe-" + a).contentWindow || (R("minerva-xdrframe-" + a).contentDocument || R("minerva-xdrframe-" + a).contentWindow.document).parentWindow || (R("minerva-xdrframe-" + a).contentDocument || R("minerva-xdrframe-" + a).contentWindow.document).defaultView, b[1], [b[2]], a);
  this.frames.push(a);
  c.N(a)
};
var Te = new Re;
s.__XHRTracker_xdrFrameLoaded = x(Te.sf, Te);
var Ue;
Ue = m;
var Ve = Ga();
Ve && (-1 != Ve.indexOf("Firefox") || -1 != Ve.indexOf("Camino") || -1 != Ve.indexOf("iPhone") || -1 != Ve.indexOf("iPod") || -1 != Ve.indexOf("iPad") || -1 != Ve.indexOf("Android") || -1 != Ve.indexOf("Chrome") && (Ue = j));
var We = Ue;
/*
 Portions of this code are from MochiKit, received by The Closure
 Library Authors under the MIT license. All other code is Copyright
 2005-2009 The Closure Library Authors. All Rights Reserved.
*/
function Xe(a, b, c, d, g, e) {
  L.call(this, g, e);
  this.Fd = a;
  this.hc = [];
  this.nd = !!b;
  this.Ee = !!c;
  this.ve = !!d;
  for(b = 0;b < a.length;b++) {
    a[b].Y(x(this.td, this, b, j), x(this.td, this, b, m))
  }
  0 == a.length && !this.nd && this.N(this.hc)
}
A(Xe, L);
Xe.prototype.Md = 0;
Xe.prototype.td = function(a, b, c) {
  this.Md++;
  this.hc[a] = [b, c];
  this.$ || (this.nd && b ? this.N([a, c]) : this.Ee && !b ? this.P(c) : this.Md == this.Fd.length && this.N(this.hc));
  this.ve && !b && (c = k);
  return c
};
Xe.prototype.P = function(a) {
  Xe.m.P.call(this, a);
  eb(this.Fd, function(a) {
    a.cancel()
  })
};
function Ye(a, b) {
  this.rf = a;
  this.Hd = b
}
Ye.prototype.tc = 0;
Ye.prototype.Lb = 0;
Ye.prototype.mc = m;
function Ze(a) {
  var b = [];
  if(a.mc) {
    return[b, 2]
  }
  var c = a.tc, d = a.rf.responseText;
  for(a.tc = d.length;;) {
    c = d.indexOf("\n", c);
    if(-1 == c) {
      break
    }
    var g = d.substr(a.Lb, c - a.Lb), g = g.replace(/\r$/, "");
    if(g.length > a.Hd) {
      return a.mc = j, [b, 2]
    }
    b.push(g);
    a.Lb = c += 1
  }
  return a.tc - a.Lb - 1 > a.Hd ? (a.mc = j, [b, 2]) : [b, 1]
}
;function $e(a, b, c) {
  this.w = b;
  this.R = a;
  this.ec = c
}
A($e, I);
p = $e.prototype;
p.a = U("cw.net.XHRMaster");
p.qa = -1;
p.wc = function(a, b, c) {
  this.ec.__XHRSlave_makeRequest(this.R, a, b, c)
};
p.la = o("qa");
p.zc = function(a, b) {
  1 != b && this.a.H(N(this.R) + " got status != OK: " + b + "; XHRSlave should dispose soon.");
  pe(this.w);
  qe(this.w, a)
};
p.Ac = function(a) {
  this.a.j("ongotheaders_: " + N(a));
  var b = k;
  "Content-Length" in a && (b = bc(a["Content-Length"]));
  a = this.w;
  a.a.j(a.k() + " got Content-Length: " + b);
  a.X == af && (b == k && (a.a.q("Expected to receive a valid Content-Length, but did not."), b = 5E5), bf(a, 2E3 + 1E3 * (b / 3072)))
};
p.Bc = function(a) {
  1 != a && this.a.j(this.w.k() + "'s XHR's readyState is " + a);
  this.qa = a;
  2 <= this.qa && pe(this.w)
};
p.yc = function() {
  this.w.b()
};
p.d = function() {
  $e.m.d.call(this);
  delete Z.ba[this.R];
  this.ec.__XHRSlave_dispose(this.R);
  delete this.ec
};
function cf() {
  this.ba = {}
}
A(cf, I);
p = cf.prototype;
p.a = U("cw.net.XHRMasterTracker");
p.gc = function(a, b) {
  var c = "_" + Yb(), d = new $e(c, a, b);
  return this.ba[c] = d
};
p.zc = function(a, b, c) {
  if(Ka) {
    for(var d = [], g = 0, e = b.length;g < e;g++) {
      d[g] = b[g]
    }
    b = d
  }else {
    b = jb(b)
  }
  (d = this.ba[a]) ? d.zc(b, c) : this.a.H("onframes_: no master for " + N(a))
};
p.Ac = function(a, b) {
  var c = this.ba[a];
  c ? c.Ac(b) : this.a.H("ongotheaders_: no master for " + N(a))
};
p.Bc = function(a, b) {
  var c = this.ba[a];
  c ? c.Bc(b) : this.a.H("onreadystatechange_: no master for " + N(a))
};
p.yc = function(a) {
  var b = this.ba[a];
  b ? (delete this.ba[b.R], b.yc()) : this.a.H("oncomplete_: no master for " + N(a))
};
p.d = function() {
  cf.m.d.call(this);
  for(var a = Ya(this.ba);a.length;) {
    a.pop().b()
  }
  delete this.ba
};
var Z = new cf;
s.__XHRMaster_onframes = x(Z.zc, Z);
s.__XHRMaster_oncomplete = x(Z.yc, Z);
s.__XHRMaster_ongotheaders = x(Z.Ac, Z);
s.__XHRMaster_onreadystatechange = x(Z.Bc, Z);
function df(a, b, c) {
  this.V = a;
  this.host = b;
  this.port = c
}
function ef(a, b, c) {
  this.host = a;
  this.port = b;
  this.kf = c
}
function ff(a, b) {
  b || (b = a);
  this.V = a;
  this.ua = b
}
ff.prototype.v = function(a, b) {
  a.push("<HttpEndpoint primaryUrl=");
  M(this.V, a, b);
  a.push(", secondaryUrl=");
  M(this.ua, a, b);
  a.push(">")
};
function gf(a, b, c, d) {
  this.V = a;
  this.Pd = b;
  this.ua = c;
  this.Zd = d;
  (!(0 == this.V.indexOf("http://") || 0 == this.V.indexOf("https://")) || !(0 == this.ua.indexOf("http://") || 0 == this.ua.indexOf("https://"))) && f(Error("primaryUrl and secondUrl must be absolute URLs with http or https scheme"));
  a = this.Pd.location.href;
  sd(this.V, a) || f(Error("primaryWindow not same origin as primaryUrl: " + a));
  a = this.Zd.location.href;
  sd(this.ua, a) || f(Error("secondaryWindow not same origin as secondaryUrl: " + a))
}
gf.prototype.v = function(a, b) {
  a.push("<ExpandedHttpEndpoint_ primaryUrl=");
  M(this.V, a, b);
  a.push(", secondaryUrl=");
  M(this.ua, a, b);
  a.push(">")
};
var hf = new Ee(";)]}");
function jf(a) {
  s.setTimeout(function() {
    u(a.message) && a.stack && (a.message += "\n" + a.stack);
    f(a)
  }, 0)
}
function kf(a, b, c) {
  u(b) || (b = j);
  u(c) || (c = j);
  this.Va = a;
  this.nf = b;
  this.gf = c
}
p = kf.prototype;
p.a = U("cw.net.QANProtocolWrapper");
p.ib = function(a, b) {
  this.a.q(a, b);
  this.gf && jf(b)
};
p.da = function(a) {
  this.Ya.$d(zc(a), this.nf)
};
p.Bb = function(a) {
  this.Ya.reset("QANHelper said: " + a)
};
p.ef = function(a) {
  this.Ya = a;
  this.Ec = new Q(x(this.Va.bodyReceived, this.Va), x(this.ib, this), x(this.da, this), x(this.Bb, this));
  this.Va.streamStarted.call(this.Va, this.Ya, this.Ec)
};
p.df = function(a, b) {
  this.Ec.md("Stream reset applicationLevel=" + N(b) + ", reason: " + a);
  this.Va.streamReset.call(this.Va, a, b)
};
p.ff = function(a) {
  try {
    var b = Cc(a)
  }catch(c) {
    c instanceof Ac || f(c);
    this.Ya.reset("Bad QAN frame.  Did peer send a non-QAN string?");
    return
  }
  this.Ec.ud(b)
};
function lf(a) {
  this.Ya = a
}
lf.prototype.v = function(a, b) {
  a.push("<UserContext for ");
  M(this.Ya, a, b);
  a.push(">")
};
function mf(a, b, c, d) {
  P.call(this, "TransportInfo", [a, b, c, d]);
  this.fa = a
}
A(mf, P);
function $(a, b, c) {
  this.r = a;
  this.o = c ? c : Pb;
  this.pb = new Yc;
  this.ob = Yb() + Yb();
  this.W = new Nd;
  this.sc = new Pd;
  this.qb = k;
  this.Xb = [];
  this.Ia = new lf(this);
  this.qe = x(this.lf, this);
  F && (this.qb = wb(s, "load", this.Ye, m, this))
}
A($, I);
p = $.prototype;
p.a = U("cw.net.ClientStream");
p.Dd = new Md(-1, []);
p.Ed = new Md(-1, []);
p.maxUndeliveredStrings = 50;
p.maxUndeliveredBytes = 1048576;
p.onstring = k;
p.onstarted = k;
p.Cc = k;
p.Dc = k;
p.onreset = k;
p.ondisconnect = k;
p.Xa = k;
p.Lc = m;
p.Gc = m;
p.B = "1_UNSTARTED";
p.Rc = -1;
p.e = k;
p.p = k;
p.kb = k;
p.Mc = 0;
p.Od = 0;
p.Yd = 0;
p.v = function(a, b) {
  a.push("<ClientStream id=");
  M(this.ob, a, b);
  a.push(", state=", "" + this.B);
  a.push(", primary=");
  M(this.e, a, b);
  a.push(", secondary=");
  M(this.p, a, b);
  a.push(", resetting=");
  M(this.kb, a, b);
  a.push(">")
};
p.Ie = o("Ia");
p.oe = function(a) {
  u(a.streamStarted) || f(Error("Protocol is missing required method streamStarted"));
  u(a.streamReset) || f(Error("Protocol is missing required method streamReset"));
  u(a.stringReceived) || f(Error("Protocol is missing required method stringReceived"));
  this.onstarted = x(a.streamStarted, a);
  this.onreset = x(a.streamReset, a);
  this.onstring = x(a.stringReceived, a);
  this.Cc = u(a.transportCreated) ? x(a.transportCreated, a) : k;
  this.Dc = u(a.transportDestroyed) ? x(a.transportDestroyed, a) : k
};
function nf(a) {
  var b = [-1];
  a.e && b.push(a.e.Ta);
  a.p && b.push(a.p.Ta);
  return Math.max.apply(Math.max, b)
}
function of(a) {
  if(!("3_STARTED" > a.B)) {
    pf(a);
    var b = 0 != a.W.G.A(), c = Qd(a.sc), d = !c.K(a.Ed) && !(a.e && c.K(a.e.Qa) || a.p && c.K(a.p.Qa)), g = nf(a);
    if((b = b && g < a.W.ya) || d) {
      var e = b && d ? "string(s)+SACK" : b ? "string(s)" : d ? "SACK" : "nothing!?";
      a.e.xa ? (a.a.s("tryToSend_: writing " + e + " to primary"), d && (d = a.e, c != d.Qa && (!d.ea && !d.u.length && qf(d), d.u.push(new Ce(c)), d.Qa = c)), b && rf(a.e, a.W, g + 1), a.e.aa()) : a.p == k ? a.Lc ? (a.a.s("tryToSend_: creating secondary to send " + e), a.p = sf(a, m, j), a.p && (b && rf(a.p, a.W, g + 1), a.p.aa())) : (a.a.s("tryToSend_: not creating a secondary because stream might not exist on server"), a.Gc = j) : a.a.s("tryToSend_: need to send " + e + ", but can't right now")
    }
  }
}
function pf(a) {
  a.Xa != k && (a.o.z.clearTimeout(a.Xa), a.Xa = k)
}
p.lf = function() {
  this.Xa = k;
  of(this)
};
function tf(a) {
  a.Xa == k && (a.Xa = a.o.z.setTimeout(a.qe, 6))
}
p.Ye = function() {
  this.qb = k;
  if(this.e && this.e.Pa()) {
    this.a.info("restartHttpRequests_: aborting primary");
    var a = this.e;
    a.Zb = j;
    a.b()
  }
  this.p && this.p.Pa() && (this.a.info("restartHttpRequests_: aborting secondary"), a = this.p, a.Zb = j, a.b())
};
p.$d = function(a, b) {
  u(b) || (b = j);
  "3_STARTED" < this.B && f(Error("sendString: Can't send in state " + this.B));
  b && (v(a) || f(Error("sendString: not a string: " + N(a))), /^([ -~]*)$/.test(a) || f(Error("sendString: string has illegal chars: " + N(a))));
  this.W.append(a);
  tf(this)
};
function sf(a, b, c) {
  var d;
  a.r instanceof gf ? d = af : a.r instanceof ef ? d = uf : f(Error("Don't support endpoint " + N(a.r)));
  a.Rc += 1;
  b = new vf(a.o, a, a.Rc, d, a.r, b);
  a.a.s("Created: " + b.k());
  if(c) {
    if(a.Cc) {
      c = new mf(b.fa, b.ha, b.ra, b.xa);
      try {
        a.Cc.call(a.Ia, c)
      }catch(g) {
        a.a.q("ontransportcreated raised uncaught exception", g), jf(g)
      }
    }
    if(wf(a)) {
      return k
    }
  }
  a.pb.add(b);
  return b
}
function xf(a, b, c) {
  var d = new yf(a.o, a, b, c);
  a.a.s("Created: " + d.k() + ", delay=" + b + ", times=" + c);
  a.pb.add(d);
  return d
}
function zf(a, b) {
  a.pb.remove(b) || f(Error("transportOffline_: Transport was not removed?"));
  a.a.j("Offline: " + b.k());
  var c = "4_RESETTING" == a.B && b.he;
  if(b instanceof vf && !c) {
    if(a.Dc) {
      var d = new mf(b.fa, b.ha, b.ra, b.xa);
      try {
        a.Dc.call(a.Ia, d)
      }catch(g) {
        a.a.q("ontransportdestroyed raised uncaught exception", g), jf(g)
      }
    }
    if(wf(a)) {
      return
    }
  }
  a.Mc = b.oa ? a.Mc + b.oa : 0;
  1 <= a.Mc && (a.a.info("transportOffline_: Doing an internal reset because streamPenalty_ reached limit."), Af(a, "stream penalty reached limit", m), a.b());
  if("3_STARTED" < a.B) {
    c ? (a.a.j("Disposing because resettingTransport_ is done."), a.b()) : a.a.j("Not creating a transport because ClientStream is in state " + a.B)
  }else {
    c = b instanceof yf;
    if(!c && b.Zb) {
      var e = F ? We ? [0, 1] : [9, 20] : [0, 0], c = e[0], d = e[1];
      a.a.s("getDelayForNextTransport_: " + N({delay:c, times:d}))
    }else {
      if(d = b.bd(), b == a.e ? d ? e = ++a.Od : c || (e = a.Od = 0) : d ? e = ++a.Yd : c || (e = a.Yd = 0), c || !e) {
        d = c = 0, a.a.s("getDelayForNextTransport_: " + N({count:e, delay:c, times:d}))
      }else {
        var h = 2E3 * Math.min(e, 3), l = Math.floor(4E3 * Math.random()) - 2E3, n = Math.max(0, b.fe - b.Sc), d = (c = Math.max(0, h + l - n)) ? 1 : 0;
        a.a.s("getDelayForNextTransport_: " + N({count:e, base:h, variance:l, oldDuration:n, delay:c, times:d}))
      }
    }
    c = [c, d];
    e = c[0];
    c = c[1];
    if(b == a.e) {
      a.e = k;
      if(c) {
        a.e = xf(a, e, c)
      }else {
        e = nf(a);
        a.e = sf(a, j, j);
        if(!a.e) {
          return
        }
        rf(a.e, a.W, e + 1)
      }
      a.e.aa()
    }else {
      b == a.p && (a.p = k, c ? (a.p = xf(a, e, c), a.p.aa()) : of(a))
    }
  }
}
function Af(a, b, c) {
  if(a.onreset) {
    try {
      a.onreset.call(a.Ia, b, c)
    }catch(d) {
      a.a.q("onreset raised uncaught exception", d), jf(d)
    }
  }
}
p.reset = function(a) {
  "3_STARTED" < this.B && f(Error("reset: Can't send reset in state " + this.B));
  pf(this);
  0 != this.W.G.A() && this.a.q("reset: strings in send queue will never be sent: " + N(this.W));
  this.B = "4_RESETTING";
  this.e && this.e.xa ? (this.a.info("reset: Sending ResetFrame over existing primary."), Bf(this.e, a), this.e.aa()) : (this.e && (this.a.j("reset: Disposing primary before sending ResetFrame."), this.e.b()), this.p && (this.a.j("reset: Disposing secondary before sending ResetFrame."), this.p.b()), this.a.info("reset: Creating resettingTransport_ for sending ResetFrame."), this.kb = sf(this, m, m), Bf(this.kb, a), this.kb.aa());
  Af(this, a, j)
};
function wf(a) {
  return"4_RESETTING" == a.B || a.ja
}
p.jd = function(a) {
  this.a.H("Failed to start " + N(this) + "; error was " + N(a.message));
  this.b();
  return k
};
p.start = function() {
  this.onmessage && f(Error("ClientStream.start: Hey, you! It's `onstring`, not `onmessage`! Refusing to start."));
  "1_UNSTARTED" != this.B && f(Error("ClientStream.start: " + N(this) + " already started"));
  if(this.onstarted) {
    this.onstarted(this)
  }
  this.B = "2_WAITING_RESOURCES";
  if(this.r instanceof ff) {
    var a = Se(this.r.V, this), b = Se(this.r.ua, this), a = new Xe([a, b], m, j);
    a.La(function(a) {
      return fb(a, function(a) {
        return a[1]
      })
    });
    a.La(x(this.Ce, this));
    a.sb(x(this.jd, this))
  }else {
    if(this.r instanceof df) {
      if(rc) {
        this.ld()
      }else {
        a = this.o;
        b = this.r.V;
        if(ve.length) {
          a = we()
        }else {
          b = new ke(b + "FlashConnector.swf?cb=4bdfc178fc0e508c0cd5efc3fdb09920");
          b.Xc = "#777777";
          le(b, 300, 30);
          var c = R("minerva-elements");
          c || f(Error('loadFlashConnector_: Page is missing an empty div with id "minerva-elements"; please add one.'));
          var d = R("minerva-elements-FlashConnectorSwf");
          d || (d = Sc("div", {id:"minerva-elements-FlashConnectorSwf"}), c.appendChild(d));
          var g = a.z, e;
          var a = d, h, l = function() {
            h && delete s.__loadFlashObject_callbacks[h]
          };
          if(Ka && !G("1.8.1.20")) {
            e = Nb(new me("Flash corrupts Error hierarchy in Firefox 2.0.0.0; disabled for all < 2.0.0.20"))
          }else {
            if(0 <= ya(ce, "9")) {
              var n;
              h = "_" + Yb();
              var q = new L(l);
              s.__loadFlashObject_callbacks[h] = function() {
                g.setTimeout(function() {
                  l();
                  q.N(R(n))
                }, 0)
              };
              b.Cb.set("onloadcallback", '__loadFlashObject_callbacks["' + h + '"]()');
              n = he(b);
              b.Da && f(Error("Component already rendered"));
              b.h || b.bb();
              a ? a.insertBefore(b.h, k) : b.xb.za.body.appendChild(b.h);
              (!b.t || b.t.Da) && b.yb();
              e = q
            }else {
              e = Nb(new me("Need Flash Player 9+; had " + (ce ? ce : "none")))
            }
          }
          var z = g.setTimeout(function() {
            e.cancel()
          }, 8E3);
          e.Vc(function(a) {
            g.clearTimeout(z);
            return a
          });
          qc = e;
          a = we();
          qc.Y(xe, ye)
        }
        var r = this;
        a.La(function(a) {
          rc || (rc = new te(r.o, a));
          return k
        });
        a.La(x(this.ld, this));
        a.sb(x(this.jd, this))
      }
    }else {
      Cf(this)
    }
  }
};
p.Ce = function(a) {
  var b = a[0].contentWindow, c = a[1].contentWindow, d = a[0].Ab, g = a[1].Ab;
  this.Xb.push(a[0]);
  this.Xb.push(a[1]);
  this.r = new gf(d, b, g, c);
  Cf(this)
};
p.ld = function() {
  this.r = new ef(this.r.host, this.r.port, rc);
  Cf(this)
};
function Cf(a) {
  a.B = "3_STARTED";
  a.e = sf(a, j, j);
  a.e && (rf(a.e, a.W, k), a.e.aa())
}
p.d = function() {
  this.a.info(N(this) + " in disposeInternal.");
  pf(this);
  this.B = "5_DISCONNECTED";
  for(var a = this.pb.C(), b = 0;b < a.length;b++) {
    a[b].b()
  }
  for(a = 0;a < this.Xb.length;a++) {
    ib(this.Xb[a].Oc, this)
  }
  F && this.qb && (yb(this.qb), this.qb = k);
  this.ondisconnect && this.ondisconnect.call(this.Ia);
  delete this.pb;
  delete this.e;
  delete this.p;
  delete this.kb;
  delete this.Ia;
  $.m.d.call(this)
};
var af = 1, uf = 3;
function vf(a, b, c, d, g, e) {
  this.o = a;
  this.D = b;
  this.fa = c;
  this.X = d;
  this.r = g;
  this.u = [];
  this.ha = e;
  this.xa = !this.Pa();
  this.ra = this.X != af;
  this.pe = x(this.hf, this)
}
A(vf, I);
p = vf.prototype;
p.a = U("cw.net.ClientTransport");
p.i = k;
p.Sc = k;
p.fe = k;
p.Qb = k;
p.ea = m;
p.Ub = m;
p.Qa = k;
p.Db = 0;
p.Ta = -1;
p.Nb = -1;
p.he = m;
p.Zb = m;
p.oa = 0;
p.eb = m;
p.v = function(a) {
  a.push("<ClientTransport #", "" + this.fa, ", becomePrimary=", "" + this.ha, ">")
};
p.k = function() {
  return(this.ha ? "Prim. T#" : "Sec. T#") + this.fa
};
p.bd = function() {
  return!(!this.eb && this.Db)
};
p.Pa = function() {
  return this.X == af || 2 == this.X
};
function Df(a, b) {
  H.sort.call(b, function(a, b) {
    return a[0] > b[0] ? 1 : a[0] < b[0] ? -1 : 0
  } || lb);
  a: {
    var c = a.D, d = !a.ra, g, e = c.sc;
    g = c.maxUndeliveredStrings;
    for(var h = c.maxUndeliveredBytes, l = [], n = m, q = 0, z = b.length;q < z;q++) {
      var r = b[q], w = r[0], r = r[1];
      if(w == e.Ea + 1) {
        e.Ea += 1;
        for(l.push(r);;) {
          w = e.Ea + 1;
          r = e.wa.get(w, Rd);
          if(r === Rd) {
            break
          }
          l.push(r[0]);
          e.wa.remove(w);
          e.I -= r[1];
          e.Ea = w
        }
      }else {
        if(!(w <= e.Ea)) {
          if(g != k && e.wa.A() >= g) {
            n = j;
            break
          }
          var E = Ld(r);
          if(h != k && e.I + E > h) {
            n = j;
            break
          }
          e.wa.set(w, [r, E]);
          e.I += E
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
            c.onstring.call(c.Ia, l)
          }catch(lc) {
            c.a.q("onstring raised uncaught exception", lc), jf(lc)
          }
        }
        if(wf(c)) {
          break a
        }
      }
    }
    d || tf(c);
    !wf(c) && g && (a.a.H(a.k() + "'s peer caused rwin overflow."), a.b())
  }
}
function Ef(a, b, c) {
  try {
    var d = Pe(b);
    a.Db += 1;
    a.a.j(a.k() + " RECV " + N(d));
    var g;
    1 == a.Db && !d.K(hf) && a.Pa() ? (a.a.q(a.k() + " is closing soon because got bad preamble: " + N(d)), g = j) : g = m;
    if(g) {
      return j
    }
    if(d instanceof De) {
      if(!/^([ -~]*)$/.test(d.Pc)) {
        return a.eb = j
      }
      a.Nb += 1;
      c.push([a.Nb, d.Pc])
    }else {
      if(d instanceof Ce) {
        var e = a.D, h = d.sa;
        e.Dd = h;
        var l = e.W, n = h.Ka, c = m;
        n > l.ya && (c = j);
        for(var q = Od(l).concat(), d = 0;d < q.length;d++) {
          var z = q[d];
          if(z > n) {
            break
          }
          var r = l.G.get(z)[1];
          l.G.remove(z);
          l.I -= r
        }
        for(d = 0;d < h.Ga.length;d++) {
          var w = h.Ga[d];
          w > l.ya && (c = j);
          l.G.Z(w) && (r = l.G.get(w)[1], l.G.remove(w), l.I -= r)
        }
        l.G.fb() && l.G.clear();
        if(c) {
          return a.a.q(a.k() + " is closing soon because got bad SackFrame"), a.eb = j
        }
      }else {
        if(d instanceof Fe) {
          a.Nb = d.ae - 1
        }else {
          if(d instanceof He) {
            a.D.Ed = d.Cd
          }else {
            if(d instanceof Je) {
              return a.a.s(a.k() + " is closing soon because got YouCloseItFrame"), j
            }
            if(d instanceof Oe) {
              return a.eb = j, "stream_attach_failure" == d.reason ? a.oa += 1 : "acked_unsent_strings" == d.reason && (a.oa += 0.5), a.a.s(a.k() + " is closing soon because got " + N(d)), j
            }
            if(!(d instanceof Ee)) {
              if(d instanceof Ie) {
                var E = a.D, lc = !a.ra;
                E.a.s("Stream is now confirmed to exist at server.");
                E.Lc = j;
                E.Gc && !lc && (E.Gc = m, of(E))
              }else {
                if(c.length) {
                  Df(a, c);
                  if(!fa(c)) {
                    for(var vd = c.length - 1;0 <= vd;vd--) {
                      delete c[vd]
                    }
                  }
                  c.length = 0
                }
                if(d instanceof Ke) {
                  var Le = a.D;
                  Af(Le, d.Td, d.Wc);
                  Le.b();
                  return j
                }
                f(Error(a.k() + " had unexpected state in framesReceived_."))
              }
            }
          }
        }
      }
    }
  }catch(Me) {
    return Me instanceof X || f(Me), a.a.q(a.k() + " is closing soon because got InvalidFrame: " + N(b)), a.eb = j
  }
  return m
}
function qe(a, b) {
  a.Ub = j;
  try {
    for(var c = m, d = [], g = 0, e = b.length;g < e;g++) {
      if(a.ja) {
        a.a.info(a.k() + " returning from loop because we're disposed.");
        return
      }
      if(c = Ef(a, b[g], d)) {
        break
      }
    }
    d.length && Df(a, d);
    a.Ub = m;
    a.u.length && a.aa();
    c && (a.a.s(a.k() + " closeSoon is true.  Frames were: " + N(b)), a.b())
  }finally {
    a.Ub = m
  }
}
p.hf = function() {
  this.a.q(this.k() + " timed out due to lack of connection or no data being received.");
  this.b()
};
function Ff(a) {
  a.Qb != k && (a.o.z.clearTimeout(a.Qb), a.Qb = k)
}
function bf(a, b) {
  Ff(a);
  b = Math.round(b);
  a.Qb = a.o.z.setTimeout(a.pe, b);
  a.a.j(a.k() + "'s receive timeout set to " + b + " ms.")
}
function pe(a) {
  a.X != af && (a.X == uf || 2 == a.X ? bf(a, 13500) : f(Error("peerStillAlive_: Don't know what to do for this transportType: " + a.X)))
}
function qf(a) {
  var b = new Ae;
  b.fa = a.fa;
  b.Qd = 2;
  b.wd = 2;
  a.D.Lc || (b.Vd = j);
  b.ob = a.D.ob;
  b.Nc = a.ra;
  b.Nc && (b.Kd = 4096);
  b.Id = 3E5;
  b.Gd = a.ra ? Math.floor(10) : 0;
  b.ge = m;
  a.ha && (b.de = k, b.xc = Math.floor((a.ra ? 358E4 : 25E3) / 1E3));
  b.sa = Qd(a.D.sc);
  b.Ib = a.D.Dd;
  a.u.push(b);
  a.Qa = b.sa
}
function re(a, b) {
  b && (a.oa += 0.5);
  a.b()
}
p.aa = function() {
  this.ea && !this.xa && f(Error("flush_: Can't flush more than once to this transport."));
  if(this.Ub) {
    this.a.s(this.k() + " flush_: Returning because spinning right now.")
  }else {
    var a = this.ea;
    this.ea = j;
    !a && !this.u.length && qf(this);
    for(a = 0;a < this.u.length;a++) {
      this.a.j(this.k() + " SEND " + N(this.u[a]))
    }
    if(this.Pa()) {
      for(var a = [], b = 0, c = this.u.length;b < c;b++) {
        this.u[b].O(a), a.push("\n")
      }
      this.u = [];
      a = a.join("");
      b = this.ha ? this.r.V : this.r.ua;
      this.i = Z.gc(this, this.ha ? this.r.Pd : this.r.Zd);
      this.Sc = this.o.z === Eb ? pa() : this.o.z.getTime();
      this.i.wc(b, "POST", a);
      bf(this, 3E3 * (1.5 + (0 == b.indexOf("https://") ? 3 : 1)) + 4E3 + (this.ra ? 0 : this.ha ? 25E3 : 0))
    }else {
      if(this.X == uf) {
        a = [];
        b = 0;
        for(c = this.u.length;b < c;b++) {
          a.push(this.u[b].J())
        }
        this.u = [];
        this.i ? this.i.rb(a) : (b = this.r, this.i = new ue(this), this.i.Tb = b.kf.gc(this.i), this.Sc = this.o.z === Eb ? pa() : this.o.z.getTime(), this.i.cc(b.host, b.port), this.i.ja || (this.i.rb(a), this.i.ja || bf(this, 8E3)))
      }else {
        f(Error("flush_: Don't know what to do for this transportType: " + this.X))
      }
    }
  }
};
function rf(a, b, c) {
  !a.ea && !a.u.length && qf(a);
  for(var d = Math.max(c, a.Ta + 1), g = Od(b), c = [], e = 0;e < g.length;e++) {
    var h = g[e];
    (d == k || h >= d) && c.push([h, b.G.get(h)[0]])
  }
  b = 0;
  for(d = c.length;b < d;b++) {
    e = c[b], g = e[0], e = e[1], (-1 == a.Ta || a.Ta + 1 != g) && a.u.push(new Fe(g)), a.u.push(new De(e)), a.Ta = g
  }
}
p.d = function() {
  this.a.info(this.k() + " in disposeInternal.");
  vf.m.d.call(this);
  this.fe = this.o.z === Eb ? pa() : this.o.z.getTime();
  this.u = [];
  Ff(this);
  this.i && this.i.b();
  var a = this.D;
  this.D = k;
  zf(a, this)
};
function Bf(a, b) {
  !a.ea && !a.u.length && qf(a);
  a.u.push(new Ke(b, j));
  a.he = j
}
function yf(a, b, c, d) {
  this.o = a;
  this.D = b;
  this.hd = c;
  this.dd = d
}
A(yf, I);
p = yf.prototype;
p.ea = m;
p.xa = m;
p.Eb = k;
p.Qa = k;
p.a = U("cw.net.DoNothingTransport");
function Gf(a) {
  a.Eb = a.o.z.setTimeout(function() {
    a.Eb = k;
    a.dd--;
    a.dd ? Gf(a) : a.b()
  }, a.hd)
}
p.aa = function() {
  this.ea && !this.xa && f(Error("flush_: Can't flush more than once to DoNothingTransport."));
  this.ea = j;
  Gf(this)
};
p.v = function(a) {
  a.push("<DoNothingTransport delay=", "" + this.hd, ">")
};
p.Pa = ba(m);
p.k = ba("Wast. T");
p.bd = ba(m);
p.d = function() {
  this.a.info(this.k() + " in disposeInternal.");
  yf.m.d.call(this);
  this.Eb != k && this.o.z.clearTimeout(this.Eb);
  var a = this.D;
  this.D = k;
  zf(a, this)
};
function Hf() {
}
Hf.prototype.ub = k;
var If;
function Jf() {
}
A(Jf, Hf);
function Kf(a) {
  return(a = Lf(a)) ? new ActiveXObject(a) : new XMLHttpRequest
}
function Mf(a) {
  var b = {};
  Lf(a) && (b[0] = j, b[1] = j);
  return b
}
Jf.prototype.qc = k;
function Lf(a) {
  if(!a.qc && "undefined" == typeof XMLHttpRequest && "undefined" != typeof ActiveXObject) {
    for(var b = ["MSXML2.XMLHTTP.6.0", "MSXML2.XMLHTTP.3.0", "MSXML2.XMLHTTP", "Microsoft.XMLHTTP"], c = 0;c < b.length;c++) {
      var d = b[c];
      try {
        return new ActiveXObject(d), a.qc = d
      }catch(g) {
      }
    }
    f(Error("Could not create ActiveXObject. ActiveX might be disabled, or MSXML might not be installed"))
  }
  return a.qc
}
If = new Jf;
function Nf(a) {
  this.headers = new O;
  this.$a = a || k
}
A(Nf, Db);
Nf.prototype.a = U("goog.net.XhrIo");
var Of = /^https?$/i;
p = Nf.prototype;
p.ga = m;
p.f = k;
p.Yb = k;
p.uc = "";
p.Bd = "";
p.gb = "";
p.ic = m;
p.Gb = m;
p.rc = m;
p.Ca = m;
p.Vb = 0;
p.Ha = k;
p.Xd = "";
p.pf = m;
p.send = function(a, b, c, d) {
  this.f && f(Error("[goog.net.XhrIo] Object is active with another request"));
  b = b ? b.toUpperCase() : "GET";
  this.uc = a;
  this.gb = "";
  this.Bd = b;
  this.ic = m;
  this.ga = j;
  this.f = this.$a ? Kf(this.$a) : Kf(If);
  this.Yb = this.$a ? this.$a.ub || (this.$a.ub = Mf(this.$a)) : If.ub || (If.ub = Mf(If));
  this.f.onreadystatechange = x(this.Nd, this);
  try {
    this.a.j(Pf(this, "Opening Xhr")), this.rc = j, this.f.open(b, a, j), this.rc = m
  }catch(g) {
    this.a.j(Pf(this, "Error opening Xhr: " + g.message));
    Qf(this, g);
    return
  }
  var a = c || "", e = this.headers.S();
  d && gc(d, function(a, b) {
    e.set(b, a)
  });
  "POST" == b && !e.Z("Content-Type") && e.set("Content-Type", "application/x-www-form-urlencoded;charset=utf-8");
  gc(e, function(a, b) {
    this.f.setRequestHeader(b, a)
  }, this);
  this.Xd && (this.f.responseType = this.Xd);
  "withCredentials" in this.f && (this.f.withCredentials = this.pf);
  try {
    this.Ha && (Eb.clearTimeout(this.Ha), this.Ha = k), 0 < this.Vb && (this.a.j(Pf(this, "Will abort after " + this.Vb + "ms if incomplete")), this.Ha = Eb.setTimeout(x(this.jf, this), this.Vb)), this.a.j(Pf(this, "Sending request")), this.Gb = j, this.f.send(a), this.Gb = m
  }catch(h) {
    this.a.j(Pf(this, "Send error: " + h.message)), Qf(this, h)
  }
};
p.jf = function() {
  "undefined" != typeof ca && this.f && (this.gb = "Timed out after " + this.Vb + "ms, aborting", this.a.j(Pf(this, this.gb)), this.dispatchEvent("timeout"), this.abort(8))
};
function Qf(a, b) {
  a.ga = m;
  a.f && (a.Ca = j, a.f.abort(), a.Ca = m);
  a.gb = b;
  Rf(a);
  Sf(a)
}
function Rf(a) {
  a.ic || (a.ic = j, a.dispatchEvent("complete"), a.dispatchEvent("error"))
}
p.abort = function() {
  this.f && this.ga && (this.a.j(Pf(this, "Aborting")), this.ga = m, this.Ca = j, this.f.abort(), this.Ca = m, this.dispatchEvent("complete"), this.dispatchEvent("abort"), Sf(this))
};
p.d = function() {
  this.f && (this.ga && (this.ga = m, this.Ca = j, this.f.abort(), this.Ca = m), Sf(this, j));
  Nf.m.d.call(this)
};
p.Nd = function() {
  !this.rc && !this.Gb && !this.Ca ? this.Ue() : Tf(this)
};
p.Ue = function() {
  Tf(this)
};
function Tf(a) {
  if(a.ga && "undefined" != typeof ca) {
    if(a.Yb[1] && 4 == a.la() && 2 == Uf(a)) {
      a.a.j(Pf(a, "Local request error detected and ignored"))
    }else {
      if(a.Gb && 4 == a.la()) {
        Eb.setTimeout(x(a.Nd, a), 0)
      }else {
        if(a.dispatchEvent("readystatechange"), 4 == a.la()) {
          a.a.j(Pf(a, "Request complete"));
          a.ga = m;
          try {
            var b = Uf(a), c, d;
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
                var e = ("" + a.uc).match(rd)[1] || k;
                if(!e && self.location) {
                  var h = self.location.protocol, e = h.substr(0, h.length - 1)
                }
                g = !Of.test(e ? e.toLowerCase() : "")
              }
              c = g
            }
            if(c) {
              a.dispatchEvent("complete"), a.dispatchEvent("success")
            }else {
              var l;
              try {
                l = 2 < a.la() ? a.f.statusText : ""
              }catch(n) {
                a.a.j("Can not get status: " + n.message), l = ""
              }
              a.gb = l + " [" + Uf(a) + "]";
              Rf(a)
            }
          }finally {
            Sf(a)
          }
        }
      }
    }
  }
}
function Sf(a, b) {
  if(a.f) {
    var c = a.f, d = a.Yb[0] ? ea : k;
    a.f = k;
    a.Yb = k;
    a.Ha && (Eb.clearTimeout(a.Ha), a.Ha = k);
    b || a.dispatchEvent("ready");
    try {
      c.onreadystatechange = d
    }catch(g) {
      a.a.H("Problem encountered resetting onreadystatechange: " + g.message)
    }
  }
}
p.la = function() {
  return this.f ? this.f.readyState : 0
};
function Uf(a) {
  try {
    return 2 < a.la() ? a.f.status : -1
  }catch(b) {
    return a.a.q("Can not get status: " + b.message), -1
  }
}
p.getResponseHeader = function(a) {
  return this.f && 4 == this.la() ? this.f.getResponseHeader(a) : i
};
function Pf(a, b) {
  return b + " [" + a.Bd + " " + a.uc + " " + Uf(a) + "]"
}
;var Vf = !(D || F && !G("420+"));
function Wf(a, b) {
  this.Wb = a;
  this.R = b
}
A(Wf, I);
p = Wf.prototype;
p.i = k;
p.qa = -1;
p.sd = m;
p.vd = "Content-Length Server Date Expires Keep-Alive Content-Type Transfer-Encoding Cache-Control".split(" ");
function Xf(a) {
  var b = Ze(a.fd), c = b[0], b = b[1], d = s.parent;
  d ? (d.__XHRMaster_onframes(a.R, c, b), 1 != b && a.b()) : a.b()
}
p.Le = function() {
  Xf(this);
  if(!this.ja) {
    var a = s.parent;
    a && a.__XHRMaster_oncomplete(this.R);
    this.b()
  }
};
p.We = function() {
  var a = s.parent;
  if(a) {
    this.qa = this.i.la();
    if(2 <= this.qa && !this.sd) {
      for(var b = new O, c = this.vd.length;c--;) {
        var d = this.vd[c];
        try {
          b.set(d, this.i.f.getResponseHeader(d))
        }catch(g) {
        }
      }
      if(b.A() && (this.sd = j, a.__XHRMaster_ongotheaders(this.R, mc(b)), this.ja)) {
        return
      }
    }
    a.__XHRMaster_onreadystatechange(this.R, this.qa);
    Vf && 3 == this.qa && Xf(this)
  }else {
    this.b()
  }
};
p.wc = function(a, b, c) {
  this.i = new Nf;
  ub(this.i, "readystatechange", x(this.We, this));
  ub(this.i, "complete", x(this.Le, this));
  this.i.send(a + "io/", b, c, {"Content-Type":"application/octet-stream"});
  this.fd = new Ye(this.i.f, 1048576)
};
p.d = function() {
  Wf.m.d.call(this);
  delete this.fd;
  this.i && this.i.b();
  delete this.Wb.nb[this.R];
  delete this.Wb
};
function Yf() {
  this.nb = {}
}
A(Yf, I);
Yf.prototype.Qe = function(a, b, c, d) {
  var g = new Wf(this, a);
  this.nb[a] = g;
  g.wc(b, c, d)
};
Yf.prototype.ze = function(a) {
  (a = this.nb[a]) && a.b()
};
Yf.prototype.d = function() {
  Yf.m.d.call(this);
  for(var a = Ya(this.nb);a.length;) {
    a.pop().b()
  }
  delete this.nb
};
var Zf = new Yf;
s.__XHRSlave_makeRequest = x(Zf.Qe, Zf);
s.__XHRSlave_dispose = x(Zf.ze, Zf);
var $f = U("cw.net.demo");
function ag(a, b, c, d) {
  a = new td(document.location);
  if(c) {
    return new df(d, a.ka, s.__demo_mainSocketPort)
  }
  b ? (b = s.__demo_shared_domain, v(b) || f(Error("domain was " + N(b) + "; expected a string.")), c = a.S(), wd(c, "_____random_____." + b)) : c = a.S();
  yd(c, d);
  zd(c, "", i);
  return new ff(c.toString().replace("_____random_____", "%random%"))
}
;y("Minerva.HttpEndpoint", ff);
y("Minerva.SocketEndpoint", df);
y("Minerva.QANHelper", Q);
Q.prototype.handleQANFrame = Q.prototype.ud;
Q.prototype.ask = Q.prototype.me;
Q.prototype.notify = Q.prototype.Te;
Q.prototype.failAll = Q.prototype.md;
y("Minerva.QANProtocolWrapper", kf);
kf.prototype.streamStarted = kf.prototype.ef;
kf.prototype.streamReset = kf.prototype.df;
kf.prototype.stringReceived = kf.prototype.ff;
y("Minerva.Deferred", L);
L.prototype.cancel = L.prototype.cancel;
L.prototype.callback = L.prototype.N;
L.prototype.errback = L.prototype.P;
L.prototype.addErrback = L.prototype.sb;
L.prototype.addCallback = L.prototype.La;
L.prototype.addCallbacks = L.prototype.Y;
L.prototype.chainDeferred = L.prototype.ad;
L.prototype.awaitDeferred = L.prototype.ne;
L.prototype.branch = L.prototype.Zc;
L.prototype.addBoth = L.prototype.Vc;
L.prototype.hasFired = L.prototype.Ke;
y("Minerva.Deferred.succeed", Mb);
y("Minerva.Deferred.fail", Nb);
y("Minerva.Deferred.cancelled", function() {
  var a = new L;
  a.cancel();
  return a
});
y("Minerva.Deferred.AlreadyCalledError", Jb);
y("Minerva.Deferred.CancelledError", Fb);
y("Minerva.ClientStream", $);
$.prototype.getUserContext = $.prototype.Ie;
$.prototype.bindToProtocol = $.prototype.oe;
$.prototype.start = $.prototype.start;
$.prototype.sendString = $.prototype.$d;
$.prototype.reset = $.prototype.reset;
y("Minerva.Logger", S);
S.Level = T;
S.getLogger = U;
S.prototype.setLevel = S.prototype.Ic;
S.prototype.shout = S.prototype.$e;
S.prototype.severe = S.prototype.H;
S.prototype.warning = S.prototype.q;
S.prototype.info = S.prototype.info;
S.prototype.config = S.prototype.ue;
S.prototype.fine = S.prototype.j;
S.prototype.finer = S.prototype.De;
S.prototype.finest = S.prototype.s;
T.OFF = fd;
T.SHOUT = gd;
T.SEVERE = hd;
T.WARNING = id;
T.INFO = jd;
T.CONFIG = kd;
T.FINE = ld;
T.FINER = md;
T.FINEST = nd;
T.ALL = od;
y("Minerva.LogManager", V);
V.getRoot = V.nc;
y("Minerva.DivConsole", qd);
qd.prototype.setCapturing = qd.prototype.Ze;
y("Minerva.JSON", {});
y("Minerva.JSON.parse", function(a) {
  a = "" + a;
  if(/^\s*$/.test(a) ? 0 : /^[\],:{}\s\u2028\u2029]*$/.test(a.replace(/\\["\\\/bfnrtu]/g, "@").replace(/"[^"\\\n\r\u2028\u2029\x00-\x08\x10-\x1f\x80-\x9f]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, "]").replace(/(?:^|:|,)(?:[\s\u2028\u2029]*\[)+/g, ""))) {
    try {
      return eval("(" + a + ")")
    }catch(b) {
    }
  }
  f(Error("Invalid JSON string: " + a))
});
y("Minerva.JSON.serialize", Rb);
y("Minerva.JSON.asciify", Rb);
y("Minerva.bind", x);
y("Minerva.repr", N);
y("Minerva.theCallQueue", Pb);
y("Minerva.MINIMUM_FLASH_VERSION", "9");
y("Minerva.getEndpoint", ag);
y("Minerva.getEndpointByQueryArgs", function() {
  var a;
  a = (new td(document.location)).Q;
  var b = "http" != a.get("mode");
  if((a = Boolean(Number(a.get("useSubdomains", "0")))) && !s.__demo_shared_domain) {
    $f.q("You requested subdomains, but I cannot use them because you did not specify a domain.  Proceeding without subdomains."), a = m
  }
  return ag(0, a, b, "/_minerva/")
});

})();

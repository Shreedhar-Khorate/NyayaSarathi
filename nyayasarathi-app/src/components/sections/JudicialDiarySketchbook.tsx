'use client';

import React, { useRef, useEffect, useCallback } from 'react';
import { Scale, ZoomIn, ZoomOut, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { generateLegalSpreads, LegalSpread } from '@/lib/sketchbookCanvas';

export default function JudicialDiarySketchbook() {
  const wrapRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const sb3dRef = useRef<HTMLDivElement>(null);
  const bookRef = useRef<HTMLDivElement>(null);
  const capBoxRef = useRef<HTMLDivElement>(null);
  const hintRef = useRef<HTMLParagraphElement>(null);
  const zoomWrapRef = useRef<HTMLDivElement>(null);
  const zoomInnerRef = useRef<HTMLDivElement>(null);
  const loupeRef = useRef<HTMLDivElement>(null);
  const zReadRef = useRef<HTMLSpanElement>(null);
  const zInBtnRef = useRef<HTMLButtonElement>(null);
  const zOutBtnRef = useRef<HTMLButtonElement>(null);
  const loupeBtnRef = useRef<HTMLButtonElement>(null);

  // Core mutable references kept in sync across animation loop (zero React re-render overhead)
  const stateRef = useRef<{
    spreads: LegalSpread[];
    idx: number;
    turn: { dir: 'next' | 'prev'; from: number; to: number; t: number } | null;
    strips: HTMLDivElement[];
    view: { rx: number; ry: number; z: number; trx: number; try_: number; tz: number };
    viewActive: boolean;
    lastZ: number;
    drag: { dir: 'next' | 'prev'; x0: number; w: number; moved: number; vel: number; tPrev: number } | null;
    spring: any;
    loupeOn: boolean;
    lx: number | null;
    ly: number | null;
    lgrab: { cx: number; cy: number; lx0: number; ly0: number } | null;
    lTarget: { x: number; y: number } | null;
    raf: number | null;
    lastTime: number;
    step: (dir: 'next' | 'prev') => void;
    goTo: (i: number) => void;
    introOn: boolean;
    riffle: Array<{ bell: number; dur: number }>;
    riffleAt: number;
    endIntro: () => void;
  }>({
    spreads: [],
    idx: 0,
    turn: null,
    strips: [],
    view: { rx: 0, ry: 0, z: 1, trx: 0, try_: 0, tz: 1 },
    viewActive: false,
    lastZ: 1,
    drag: null,
    spring: null,
    loupeOn: true,
    lx: null,
    ly: null,
    lgrab: null,
    lTarget: null,
    raf: null,
    lastTime: 0,
    step: () => {},
    goTo: () => {},
    introOn: false,
    riffle: [],
    riffleAt: 0,
    endIntro: () => {},
  });

  useEffect(() => {
    // Generate high-resolution canvas textures
    const spreads = generateLegalSpreads();
    stateRef.current.spreads = spreads;

    const N = 14;
    const SPAN = 0.449;
    const BETA = 0.60;
    const TILT_X = 4.5;
    const TILT_Y = 7;
    const ZOOM_MIN = 0.9;
    const ZOOM_MAX = 1.5;
    const MAG = 2.3;
    const M = spreads.length;

    const book = bookRef.current;
    const sb3d = sb3dRef.current;
    const stage = stageRef.current;
    const loupe = loupeRef.current;
    const zoomWrap = zoomWrapRef.current;
    const zoomInner = zoomInnerRef.current;
    const capBox = capBoxRef.current;
    const hint = hintRef.current;
    const wrap = wrapRef.current;

    if (!book || !sb3d || !stage || !loupe || !zoomWrap || !zoomInner || !capBox || !wrap) return;

    let capOutEl: HTMLElement | null = null;
    let capInEl: HTMLElement | null = null;

    const el = (tag: string, className?: string) => {
      const e = document.createElement(tag);
      if (className) e.className = className;
      return e;
    };

    const imgEl = (i: number, side: string) => {
      const im = new Image();
      im.className = 'sb-half-img ' + side;
      im.draggable = false;
      im.alt = '';
      im.src = stateRef.current.spreads[i].url;
      return im;
    };

    const halfEl = (pos: 'left' | 'right', i: number) => {
      const d = el('div', 'sb-half ' + pos);
      d.appendChild(imgEl(i, pos));
      d.appendChild(el('div', 'gutter-shade ' + pos));
      return d;
    };

    const buildCurl = (dir: 'next' | 'prev', from: number, to: number) => {
      stateRef.current.strips = [];
      const c = el('div', 'curl ' + dir);
      c.style.setProperty('--n', String(N));
      c.style.setProperty('--span', String(SPAN));
      let host = c;

      for (let i = 0; i < N; i++) {
        const s = el('div', 'strip') as HTMLDivElement;
        s.style.setProperty('--i', String(i));
        const gut = 'calc(var(--bw) * 0.5)';
        const sw = 'calc(var(--bw) * ' + SPAN + ' / ' + N + ')';
        const A = 'calc(-1 * (' + gut + ' + ' + i + ' * ' + sw + '))';
        const B = 'calc(' + (i + 1) + ' * ' + sw + ' - ' + gut + ')';
        const f = el('div', 'face front');
        const b = el('div', 'face back');

        const dress = (e: HTMLElement, url: string, px: string) => {
          e.style.backgroundImage = 'url(' + url + ')';
          e.style.backgroundPositionX = px;
        };

        dress(f, stateRef.current.spreads[from].url, dir === 'next' ? A : B);
        dress(b, stateRef.current.spreads[to].url, dir === 'next' ? B : A);

        f.appendChild(el('div', 'sh'));
        f.appendChild(el('div', 'gl'));
        b.appendChild(el('div', 'sh'));
        b.appendChild(el('div', 'gl'));

        s.appendChild(f);
        s.appendChild(b);

        if (i === N - 1) s.classList.add('edge');
        host.appendChild(s);
        host = s;
        stateRef.current.strips.push(s);
      }
      return c;
    };

    const fadeCaption = (t: number) => {
      if (!capOutEl || !capInEl) return;
      const out = 1 - Math.max(0, Math.min(1, (t - 0.1) / 0.28));
      const inn = Math.max(0, Math.min(1, (t - 0.56) / 0.3));
      capOutEl.style.opacity = out.toFixed(3);
      capInEl.style.opacity = inn.toFixed(3);
    };

    const applyTurn = (t: number) => {
      const th = Math.PI * t;
      const beta = BETA * Math.sin(th);
      const D = 180 / Math.PI;
      const tt = th + beta;
      const td = (2 * beta) / N;

      sb3d.style.setProperty('--tt', (tt * D).toFixed(2) + 'deg');
      sb3d.style.setProperty('--td', (td * D).toFixed(3) + 'deg');
      sb3d.style.setProperty('--shade', Math.sin(th).toFixed(3));
      fadeCaption(t);
    };

    const layout = () => {
      sb3d.style.setProperty('--bw', book.clientWidth + 'px');
    };

    const caption = () => {
      capBox.textContent = '';
      capOutEl = capInEl = null;
      const turn = stateRef.current.turn;
      const idx = stateRef.current.idx;

      if (turn) {
        capOutEl = el('p', 'sb-caption live');
        capOutEl.textContent =
          stateRef.current.spreads[turn.from].folio + ' • ' + stateRef.current.spreads[turn.from].title;
        capBox.appendChild(capOutEl);

        capInEl = el('p', 'sb-caption live');
        capInEl.textContent =
          stateRef.current.spreads[turn.to].folio + ' • ' + stateRef.current.spreads[turn.to].title;
        capBox.appendChild(capInEl);
        fadeCaption(turn.t);
      } else {
        const p = el('p', 'sb-caption');
        p.textContent = stateRef.current.spreads[idx].folio + ' • ' + stateRef.current.spreads[idx].title;
        capBox.appendChild(p);
      }
    };

    const marks = () => {};

    const loupeSize = () => {
      return Math.round(Math.max(165, Math.min(265, book.clientWidth * 0.235)));
    };

    const bookBox = () => {
      return { x: 0, y: 0, w: book.clientWidth, h: book.clientHeight };
    };

    const syncZoomLayer = () => {
      // Never clone during active turn or intro riffle! Only sync when book is at rest
      if (stateRef.current.turn || stateRef.current.introOn) return;
      zoomInner.textContent = '';
      for (let i = 0; i < book.children.length; i++) {
        const c = book.children[i];
        if (c.classList.contains('sb-zone')) continue;
        zoomInner.appendChild(c.cloneNode(true));
      }
    };

    const placeLoupe = () => {
      const lx = stateRef.current.lx;
      const ly = stateRef.current.ly;
      if (lx === null || ly === null) return;
      const B = bookBox();
      const bw = B.w;
      const bh = B.h;
      if (!bw) return;

      const R = loupeSize() / 2;
      const bez = R * 2 * 0.058;
      loupe.style.setProperty('--lr', R * 2 + 'px');
      loupe.style.transform =
        'translate3d(' + (lx - R).toFixed(1) + 'px,' + (ly - R).toFixed(1) + 'px,0)';

      if (stateRef.current.loupeOn) loupe.classList.add('on');
      else loupe.classList.remove('on');

      const z = stateRef.current.view.z;
      const cx = bw / 2;
      const cy = bh / 2;
      const x0 = cx + (bw * 0.051 - cx) * z;
      const x1 = cx + (bw * 0.949 - cx) * z;
      const y0 = cy + (bh * 0.218 - cy) * z;
      const y1 = cy + (bh * 0.782 - cy) * z;

      const nx = Math.max(x0, Math.min(lx, x1));
      const ny = Math.max(y0, Math.min(ly, y1));
      const inside =
        lx > x0 && lx < x1 && ly > y0 && ly < y1
          ? Math.min(lx - x0, x1 - lx, ly - y0, y1 - ly)
          : -Math.hypot(lx - nx, ly - ny);

      const k = Math.max(0, Math.min(1, (inside + R * 0.3) / (R * 0.55)));
      zoomWrap.style.opacity = (stateRef.current.loupeOn ? k : 0).toFixed(3);
      if (k <= 0.002) return;

      const r = (R - bez).toFixed(1);
      const mask =
        'radial-gradient(circle ' +
        r +
        'px at ' +
        lx.toFixed(1) +
        'px ' +
        ly.toFixed(1) +
        'px,#000 calc(100% - 1px),transparent 100%)';
      zoomWrap.style.webkitMaskImage = mask;
      zoomWrap.style.maskImage = mask;

      const px = cx + (lx - cx) / z;
      const py = cy + (ly - cy) / z;
      const s = MAG * z;
      zoomInner.style.transform =
        'translate(' +
        (lx - px * s).toFixed(1) +
        'px,' +
        (ly - py * s).toFixed(1) +
        'px) scale(' +
        s.toFixed(4) +
        ')';
    };

    const restLoupe = () => {
      const b = bookBox();
      stateRef.current.lx = b.x + b.w * 0.925;
      stateRef.current.ly = b.y + b.h * 0.88;
      placeLoupe();
    };

    const paint = () => {
      book.textContent = '';
      const turn = stateRef.current.turn;
      const idx = stateRef.current.idx;

      if (!turn) {
        const f = el('div', 'sb-full');
        const im = new Image();
        im.src = stateRef.current.spreads[idx].url;
        im.alt = stateRef.current.spreads[idx].title;
        im.draggable = false;
        f.appendChild(im);
        book.appendChild(f);
        sb3d.style.setProperty('--shade', '0');
      } else {
        const next = turn.dir === 'next';
        book.appendChild(halfEl('left', next ? turn.from : turn.to));
        book.appendChild(halfEl('right', next ? turn.to : turn.from));
        book.appendChild(buildCurl(turn.dir, turn.from, turn.to));
        applyTurn(turn.t);
      }

      const a = el('button', 'sb-zone sb-prev');
      const b = el('button', 'sb-zone sb-next');
      a.setAttribute('aria-label', 'Previous folio');
      b.setAttribute('aria-label', 'Next folio');
      book.appendChild(a);
      book.appendChild(b);

      layout();
      caption();
      marks();
      syncZoomLayer();
      placeLoupe();
    };

    const kick = () => {
      if (stateRef.current.raf === null) {
        stateRef.current.lastTime = performance.now();
        stateRef.current.raf = requestAnimationFrame(tick);
      }
    };

    const shoveLoupe = (dir: 'next' | 'prev') => {
      if (!stateRef.current.loupeOn || stateRef.current.lx === null || stateRef.current.lgrab) return;
      const b = bookBox();
      const lx = stateRef.current.lx;
      const ly = stateRef.current.ly;
      if (ly === null) return;

      const nx = (b.w / 2 + (lx - b.x - b.w / 2) / stateRef.current.view.z) / b.w;
      const ny = (b.h / 2 + (ly - b.y - b.h / 2) / stateRef.current.view.z) / b.h;
      if (nx < 0.02 || nx > 0.98 || ny < 0.17 || ny > 0.83) return;

      stateRef.current.lTarget = {
        x: b.x + b.w * (dir === 'next' ? 0.12 : 0.88),
        y: b.y + b.h * 0.855,
      };
      kick();
    };

    const loupeEase = () => {
      const lTarget = stateRef.current.lTarget;
      if (!lTarget) return false;
      if (stateRef.current.lgrab) {
        stateRef.current.lTarget = null;
        return false;
      }
      const lx = stateRef.current.lx;
      const ly = stateRef.current.ly;
      if (lx === null || ly === null) return false;

      const dx = lTarget.x - lx;
      const dy = lTarget.y - ly;

      if (Math.abs(dx) < 0.5 && Math.abs(dy) < 0.5) {
        stateRef.current.lx = lTarget.x;
        stateRef.current.ly = lTarget.y;
        stateRef.current.lTarget = null;
        placeLoupe();
        return false;
      }
      stateRef.current.lx = lx + dx * 0.17;
      stateRef.current.ly = ly + dy * 0.17;
      placeLoupe();
      return true;
    };

    const animateTo = (
      target: number,
      onDone?: () => void,
      stiff?: number,
      damp?: number,
      initialV?: number
    ) => {
      stateRef.current.spring = {
        kind: 'spring',
        v: initialV || 0,
        target: target,
        done: onDone,
        k: stiff || 48,
        c: damp || 13.5,
      };
      kick();
    };

    const tweenTo = (target: number, dur: number, onDone?: () => void) => {
      stateRef.current.spring = {
        kind: 'tween',
        from: stateRef.current.turn ? stateRef.current.turn.t : 0,
        target: target,
        dur: dur,
        e: 0,
        done: onDone,
      };
      kick();
    };

    const applyView = () => {
      const v = stateRef.current.view;
      sb3d.style.setProperty('--rx', v.rx.toFixed(2) + 'deg');
      sb3d.style.setProperty('--ry', v.ry.toFixed(2) + 'deg');
      sb3d.style.setProperty('--zoom', v.z.toFixed(3));

      if (v.z !== stateRef.current.lastZ) {
        stateRef.current.lastZ = v.z;
        placeLoupe();
      }
    };

    const viewSpring = () => {
      const e = 0.14;
      let moved = false;
      const v = stateRef.current.view;

      const pairs: Array<['rx' | 'ry' | 'z', 'trx' | 'try_' | 'tz']> = [
        ['rx', 'trx'],
        ['ry', 'try_'],
        ['z', 'tz'],
      ];

      for (const [k, t] of pairs) {
        const d = v[t] - v[k];
        if (Math.abs(d) > 0.0006) {
          v[k] += d * e;
          moved = true;
        } else {
          v[k] = v[t];
        }
      }

      if (moved) applyView();
      stateRef.current.viewActive = moved;
      return moved;
    };

    const tick = (now: number) => {
      stateRef.current.raf = null;
      const dt = Math.min(0.032, (now - stateRef.current.lastTime) / 1000 || 0.016);
      stateRef.current.lastTime = now;

      if (stateRef.current.spring && stateRef.current.turn) {
        const s = stateRef.current.spring;

        if (s.kind === 'tween') {
          s.e += dt;
          const k = Math.min(1, s.e / s.dur);
          // Hermite S-curve (smoothstep): zero start/end jerk, velvet smooth acceleration & deceleration
          const easeK = k * k * (3 - 2 * k);
          stateRef.current.turn.t = s.from + (s.target - s.from) * easeK;
          applyTurn(stateRef.current.turn.t);
          if (k >= 1) {
            stateRef.current.turn.t = s.target;
            applyTurn(s.target);
            stateRef.current.spring = null;
            const d = s.done;
            if (d) d();
          }
        } else {
          const x = stateRef.current.turn.t - s.target;
          s.v += (-s.k * x - s.c * s.v) * dt;
          stateRef.current.turn.t += s.v * dt;

          if (Math.abs(stateRef.current.turn.t - s.target) < 0.002 && Math.abs(s.v) < 0.02) {
            stateRef.current.turn.t = s.target;
            stateRef.current.spring = null;
            applyTurn(stateRef.current.turn.t);
            const d = s.done;
            if (d) d();
          } else {
            applyTurn(stateRef.current.turn.t);
          }
        }
      }

      viewSpring();
      const lmoved = loupeEase();

      if ((stateRef.current.spring || stateRef.current.viewActive || lmoved) && stateRef.current.raf === null) {
        stateRef.current.raf = requestAnimationFrame(tick);
      }
    };

    const setView = (rx: number, ry: number, z: number) => {
      stateRef.current.view.trx = Math.max(-TILT_X, Math.min(TILT_X, rx));
      stateRef.current.view.try_ = Math.max(-TILT_Y, Math.min(TILT_Y, ry));
      stateRef.current.view.tz = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, z));
      stateRef.current.viewActive = true;
      kick();
      syncZoom();
    };

    const tiltTo = (cx: number, cy: number) => {
      if (stateRef.current.drag) return;
      const r = book.getBoundingClientRect();
      if (!r.width) return;
      const nx = Math.max(-1, Math.min(1, (cx - (r.left + r.width / 2)) / (r.width * 0.62)));
      const ny = Math.max(-1, Math.min(1, (cy - (r.top + r.height / 2)) / (r.height * 0.9)));
      setView(-ny * TILT_X, nx * TILT_Y, stateRef.current.view.tz);
    };

    const hideHint = () => {
      if (hint) hint.classList.add('gone');
    };

    const startTurn = (dir: 'next' | 'prev', t: number, toIdx?: number) => {
      stateRef.current.spring = null;
      if (stateRef.current.turn) {
        stateRef.current.idx = stateRef.current.turn.to;
        stateRef.current.turn = null;
      }
      shoveLoupe(dir);
      const from = stateRef.current.idx;
      const to = toIdx !== undefined
        ? toIdx
        : dir === 'next' ? (from + 1) % M : (from - 1 + M) % M;
      stateRef.current.turn = {
        dir: dir,
        from: from,
        to: to,
        t: t || 0,
      };
      paint();
    };

    const commit = (initialV?: number) => {
      if (!stateRef.current.turn) return;
      if (initialV !== undefined || stateRef.current.turn.t > 0.05) {
        animateTo(
          1,
          () => {
            if (stateRef.current.turn) {
              stateRef.current.idx = stateRef.current.turn.to;
              stateRef.current.turn = null;
              paint();
            }
          },
          48,
          13.5,
          initialV
        );
      } else {
        // Snappy, buttery-smooth 360ms cubic ease-in-out turn for clicks
        tweenTo(1, 0.36, () => {
          if (stateRef.current.turn) {
            stateRef.current.idx = stateRef.current.turn.to;
            stateRef.current.turn = null;
            paint();
          }
        });
      }
      kick();
    };

    const cancel = (initialV?: number) => {
      if (!stateRef.current.turn) return;
      animateTo(
        0,
        () => {
          stateRef.current.turn = null;
          paint();
        },
        52,
        14,
        initialV
      );
      kick();
    };

    const endIntro = () => {
      stateRef.current.introOn = false;
      wrap.classList.remove('intro', 'b2');
    };
    stateRef.current.endIntro = endIntro;

    const step = (dir: 'next' | 'prev') => {
      if (stateRef.current.introOn) endIntro();
      if (stateRef.current.turn) {
        stateRef.current.idx = stateRef.current.turn.to;
        stateRef.current.turn = null;
      }
      startTurn(dir, 0);
      commit();
    };
    stateRef.current.step = step;

    const goTo = (i: number) => {
      if (stateRef.current.introOn) endIntro();
      if (i === stateRef.current.idx) return;
      if (stateRef.current.turn) {
        stateRef.current.idx = stateRef.current.turn.to;
        stateRef.current.turn = null;
      }
      const fwd = (i - stateRef.current.idx + M) % M;
      const back = (stateRef.current.idx - i + M) % M;
      const dir = fwd <= back ? 'next' : 'prev';
      startTurn(dir, 0, i);
      commit();
    };
    stateRef.current.goTo = goTo;

    // ── Opening Rapid Riffle Effect ──
    const riffleStep = () => {
      const riffle = stateRef.current.riffle;
      const at = stateRef.current.riffleAt;
      if (!riffle || at >= riffle.length || !stateRef.current.introOn) {
        endIntro();
        paint();
        return;
      }

      const s = riffle[at];
      wrap.classList.toggle('b2', s.bell > 0.55);
      startTurn('next', 0);

      tweenTo(1, s.dur, () => {
        if (stateRef.current.turn) {
          stateRef.current.idx = stateRef.current.turn.to;
          stateRef.current.turn = null;
        }
        stateRef.current.riffleAt++;
        if (stateRef.current.introOn && stateRef.current.riffleAt < riffle.length) {
          riffleStep();
        } else {
          endIntro();
          paint();
        }
      });
    };

    const startIntro = () => {
      const coarse = matchMedia('(max-width: 640px), (pointer: coarse)').matches;
      const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (coarse || reduced) {
        paint();
        return;
      }

      // Fast, smooth riffle: 5 responsive flips through the book
      const steps = 5;
      const riffle: Array<{ bell: number; dur: number }> = [];

      for (let r = 0; r < steps; r++) {
        const bell = Math.sin(Math.PI * (r / (steps - 1)));
        riffle.push({ bell: bell, dur: 0.16 - 0.07 * bell });
      }

      stateRef.current.riffle = riffle;
      stateRef.current.riffleAt = 0;
      stateRef.current.introOn = true;
      wrap.classList.add('intro');
      riffleStep();
    };

    const syncZoom = () => {
      if (zReadRef.current) {
        zReadRef.current.textContent = Math.round(stateRef.current.view.tz * 100) + '%';
      }
      if (zOutBtnRef.current) {
        zOutBtnRef.current.disabled = stateRef.current.view.tz <= ZOOM_MIN + 0.001;
      }
      if (zInBtnRef.current) {
        zInBtnRef.current.disabled = stateRef.current.view.tz >= ZOOM_MAX - 0.001;
      }
    };

    // ── Event Handlers ──
    const handlePointerDown = (e: PointerEvent) => {
      if (e.button !== 0) return;
      if (stateRef.current.introOn) endIntro();
      const onBook = (e.target as HTMLElement).closest('.sb-zone');
      stage.setPointerCapture(e.pointerId);
      hideHint();
      if (!onBook) return;

      const r = book.getBoundingClientRect();
      const dir = (e.clientX - r.left) / r.width > 0.5 ? 'next' : 'prev';
      startTurn(dir, 0);
      stateRef.current.drag = {
        dir: dir,
        x0: e.clientX,
        w: r.width,
        moved: 0,
        vel: 0,
        tPrev: performance.now(),
      };
    };

    const handlePointerMove = (e: PointerEvent) => {
      const drag = stateRef.current.drag;
      if (!drag) return;

      const dx = e.clientX - drag.x0;
      drag.moved = Math.max(drag.moved, Math.abs(dx));
      const raw = (drag.dir === 'next' ? -dx : dx) / (drag.w * 0.62);
      const t = Math.max(0, Math.min(1, raw));
      const now = performance.now();
      drag.vel = (t - (stateRef.current.turn ? stateRef.current.turn.t : 0)) / Math.max(0.001, (now - drag.tPrev) / 1000);
      drag.tPrev = now;

      if (stateRef.current.turn) {
        stateRef.current.turn.t = t;
        applyTurn(t);
      }
    };

    const handlePointerUp = () => {
      const drag = stateRef.current.drag;
      if (!drag) return;
      stateRef.current.drag = null;
      if (!stateRef.current.turn) return;

      if (drag.moved < 6) {
        commit();
        return;
      }
      const go = stateRef.current.turn.t > 0.42 || drag.vel > 0.8;
      if (go) commit(drag.vel);
      else cancel(drag.vel);
    };

    // Loupe interaction
    const handleLoupeDown = (e: PointerEvent) => {
      if (!stateRef.current.loupeOn || e.button !== 0) return;
      if (stateRef.current.introOn) endIntro();
      e.preventDefault();
      e.stopPropagation();
      stateRef.current.lTarget = null;
      stateRef.current.lgrab = {
        cx: e.clientX,
        cy: e.clientY,
        lx0: stateRef.current.lx ?? (book.clientWidth * 0.88),
        ly0: stateRef.current.ly ?? (book.clientHeight * 0.855),
      };
      loupe.classList.add('held');
      loupe.setPointerCapture(e.pointerId);
      hideHint();
    };

    const handleLoupeMove = (e: PointerEvent) => {
      const lgrab = stateRef.current.lgrab;
      if (!lgrab) return;
      const b = bookBox();
      const R = loupeSize() / 2;
      stateRef.current.lx = Math.max(b.x - R * 0.7, Math.min(b.x + b.w + R * 0.7, lgrab.lx0 + (e.clientX - lgrab.cx)));
      stateRef.current.ly = Math.max(b.y - R * 0.7, Math.min(b.y + b.h + R * 1.0, lgrab.ly0 + (e.clientY - lgrab.cy)));
      placeLoupe();
    };

    const handleLoupeUp = () => {
      stateRef.current.lgrab = null;
      loupe.classList.remove('held');
    };

    const handleGlobalPointerMove = (e: PointerEvent) => {
      if (e.pointerType === 'touch') return;
      tiltTo(e.clientX, e.clientY);
    };

    const handleGlobalPointerOut = (e: PointerEvent) => {
      if (!e.relatedTarget) setView(0, 0, stateRef.current.view.tz);
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const t = e.target as HTMLElement;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
      e.preventDefault();
      hideHint();
      step(e.key === 'ArrowRight' ? 'next' : 'prev');
    };

    const handleResize = () => {
      layout();
      stateRef.current.lx = null;
      restLoupe();
    };

    const handleDblClick = () => {
      setView(stateRef.current.view.trx, stateRef.current.view.try_, 1);
    };

    // Attach listeners
    stage.addEventListener('pointerdown', handlePointerDown);
    stage.addEventListener('pointermove', handlePointerMove);
    stage.addEventListener('pointerup', handlePointerUp);
    stage.addEventListener('pointercancel', handlePointerUp);
    stage.addEventListener('dblclick', handleDblClick);

    loupe.addEventListener('pointerdown', handleLoupeDown);
    loupe.addEventListener('pointermove', handleLoupeMove);
    loupe.addEventListener('pointerup', handleLoupeUp);
    loupe.addEventListener('pointercancel', handleLoupeUp);

    window.addEventListener('pointermove', handleGlobalPointerMove, { passive: true });
    window.addEventListener('pointerout', handleGlobalPointerOut);
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('resize', handleResize);

    // Initial paint & setup
    paint();
    applyView();
    syncZoom();
    restLoupe();

    // Pre-decode all spreads in parallel for butter-smooth 60fps flips
    Promise.all(
      spreads.map((s) => {
        const img = new Image();
        img.src = s.url;
        return img.decode ? img.decode().catch(() => {}) : Promise.resolve();
      })
    ).then(() => {
      // Trigger the opening rapid riffle animation
      setTimeout(startIntro, 320);
    });

    return () => {
      stage.removeEventListener('pointerdown', handlePointerDown);
      stage.removeEventListener('pointermove', handlePointerMove);
      stage.removeEventListener('pointerup', handlePointerUp);
      stage.removeEventListener('pointercancel', handlePointerUp);
      stage.removeEventListener('dblclick', handleDblClick);

      loupe.removeEventListener('pointerdown', handleLoupeDown);
      loupe.removeEventListener('pointermove', handleLoupeMove);
      loupe.removeEventListener('pointerup', handleLoupeUp);
      loupe.removeEventListener('pointercancel', handleLoupeUp);

      window.removeEventListener('pointermove', handleGlobalPointerMove);
      window.removeEventListener('pointerout', handleGlobalPointerOut);
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('resize', handleResize);

      if (stateRef.current.raf) {
        cancelAnimationFrame(stateRef.current.raf);
      }
    };
  }, []);

  const handleStep = useCallback((dir: 'next' | 'prev') => {
    stateRef.current.step(dir);
  }, []);


  const handleZoomIn = () => {
    const v = stateRef.current.view;
    v.tz = Math.min(1.5, v.tz * 1.16);
    stateRef.current.viewActive = true;
    if (sb3dRef.current) {
      sb3dRef.current.style.setProperty('--zoom', v.tz.toFixed(3));
    }
    if (zReadRef.current) {
      zReadRef.current.textContent = Math.round(v.tz * 100) + '%';
    }
    if (hintRef.current) hintRef.current.classList.add('gone');
  };

  const handleZoomOut = () => {
    const v = stateRef.current.view;
    v.tz = Math.max(0.9, v.tz / 1.16);
    stateRef.current.viewActive = true;
    if (sb3dRef.current) {
      sb3dRef.current.style.setProperty('--zoom', v.tz.toFixed(3));
    }
    if (zReadRef.current) {
      zReadRef.current.textContent = Math.round(v.tz * 100) + '%';
    }
    if (hintRef.current) hintRef.current.classList.add('gone');
  };

  const handleToggleLoupe = () => {
    stateRef.current.loupeOn = !stateRef.current.loupeOn;
    if (loupeBtnRef.current) {
      loupeBtnRef.current.setAttribute('aria-pressed', String(stateRef.current.loupeOn));
    }
    if (loupeRef.current) {
      loupeRef.current.classList.toggle('on', stateRef.current.loupeOn);
    }
    if (stateRef.current.loupeOn && stateRef.current.lx === null) {
      const book = bookRef.current;
      if (book) {
        stateRef.current.lx = book.clientWidth * 0.88;
        stateRef.current.ly = book.clientHeight * 0.855;
      }
    }
  };

  return (
    <section className="relative w-full py-16 px-4 md:px-8 bg-gradient-to-b from-[#151716] via-[#1D211F] to-[#151716] overflow-hidden border-y border-[#3B3A33]/50">
      {/* Background ambient lighting */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[900px] h-[550px] bg-gradient-to-b from-[#B59A68]/[0.04] to-transparent rounded-full blur-3xl" />
        <div className="absolute -bottom-24 left-1/3 w-96 h-96 bg-[#6E2634]/[0.05] rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 mx-auto max-w-7xl">
        {/* Section Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-[#B59A68]/35 bg-[#242925]/80 text-[#B59A68] text-xs font-mono uppercase tracking-widest mb-3.5 shadow-sm">
            <Scale className="w-3.5 h-3.5 text-[#B59A68]" />
            <span>Interactive Platform Handbook</span>
          </div>
          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-semibold text-[#F4EFE5] tracking-tight">
            How NyayaSarathi Works
          </h2>
          <p className="mt-3 text-stone/80 font-sans text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
            Turn the folios to inspect each core platform feature and its four-step workflow. Pick up the precision magnifying glass to examine details, algorithms, and ground-truth verifications.
          </p>
        </div>

        {/* ── 3D Sketchbook Hero Container ── */}
        <div className="sb-wrap" id="sbWrap" ref={wrapRef}>

          <div className="sb-stage" id="sbStage" ref={stageRef}>
            {/* Left Page Turn Button */}
            <button
              suppressHydrationWarning
              className="sb-arrow left"
              id="sbLeft"
              onClick={() => handleStep('prev')}
              aria-label="Previous folio"
            >
              <ChevronLeft className="w-8 h-8" strokeWidth={1.5} />
            </button>

            {/* 3D Perspective Box */}
            <div className="sb-3d" id="sb3d" ref={sb3dRef}>
              <div className="sb-tilt" id="sbTilt">
                <div className="sb-cast ambient" aria-hidden="true" />
                <div className="sb-cast contact" aria-hidden="true" />
                <div className="sb-cast hair" aria-hidden="true" />
                <div className="sb-book" id="sbBook" ref={bookRef} />
              </div>

              {/* Magnified zoom layer mirror */}
              <div className="zoomwrap" id="zoomWrap" ref={zoomWrapRef} aria-hidden="true">
                <div className="zoominner" id="zoomInner" ref={zoomInnerRef} />
              </div>

              {/* Precision Loupe (Magnifying Glass) */}
              <div className="loupe on" id="loupe" ref={loupeRef}>
                <span className="grip" />
                <span className="ring">
                  <span className="lens" id="loupeLens">
                    <span className="mag" id="loupeMag" />
                  </span>
                </span>
              </div>
            </div>

            {/* Right Page Turn Button */}
            <button
              suppressHydrationWarning
              className="sb-arrow right"
              id="sbRight"
              onClick={() => handleStep('next')}
              aria-label="Next folio"
            >
              <ChevronRight className="w-8 h-8" strokeWidth={1.5} />
            </button>
          </div>

          {/* Dynamic Captions */}
          <div className="sb-captions" id="sbCaptions" ref={capBoxRef} />

          {/* View Controls Pill */}
          <div className="sb-tools" role="group" aria-label="View Controls">
            <button
              suppressHydrationWarning
              className="tool"
              id="zOut"
              ref={zOutBtnRef}
              onClick={handleZoomOut}
              aria-label="Zoom out"
            >
              <ZoomOut />
            </button>
            <span className="zoom-read" id="zRead" ref={zReadRef} suppressHydrationWarning>
              100%
            </span>
            <button
              suppressHydrationWarning
              className="tool"
              id="zIn"
              ref={zInBtnRef}
              onClick={handleZoomIn}
              aria-label="Zoom in"
            >
              <ZoomIn />
            </button>
            <span className="tool-sep" aria-hidden="true" />
            <button
              suppressHydrationWarning
              className="tool"
              id="loupeBtn"
              ref={loupeBtnRef}
              onClick={handleToggleLoupe}
              aria-label="Toggle Magnifier Glass"
              aria-pressed="true"
            >
              <Search />
            </button>
          </div>

          {/* Interaction Cue */}
          <p className="sb-hint" id="sbHint" ref={hintRef}>
            Drag the page to turn • Drag the brass glass across the text to magnify
          </p>
        </div>
      </div>
    </section>
  );
}

"""Generator diagramow C4 (SVG) dla micro:bit Arcade Ranking.

Uzycie: py docs/c4/rysuj_diagramy.py docs/c4
"""
import html
import math
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

FONT = "'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "Consolas, 'Courier New', monospace"

FILL = {"person": "#08427B", "system": "#1168BD", "container": "#438DD5",
        "db": "#438DD5", "component": "#85BBF0"}
STROKE = {"person": "#073B6F", "system": "#0B4884", "container": "#2E6295",
          "db": "#2E6295", "component": "#5D82A8"}
INK = {"person": "#FFFFFF", "system": "#FFFFFF", "container": "#FFFFFF",
       "db": "#FFFFFF", "component": "#0B2440"}
SUB = {"person": "#D6E4F5", "system": "#DCE9F7", "container": "#E6EFF9",
       "db": "#E6EFF9", "component": "#1F3B5C"}
LINE = "#6B6B6B"


def e(s):
    return html.escape(s, quote=True)


def wrap(text, width, size, factor=0.55):
    maxc = max(6, int(width / (size * factor)))
    out, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > maxc:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    if cur:
        out.append(cur)
    return out


def txt(x, y, s, size, fill, weight="normal", anchor="middle", family=FONT, italic=False):
    st = ' font-style="italic"' if italic else ""
    if family == MONO:
        st += ' xml:space="preserve"'
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{st}>{e(s)}</text>')


class El:
    def __init__(self, kind, x, y, w, h, name, typ, desc):
        self.kind, self.x, self.y, self.w, self.h = kind, x, y, w, h
        self.name, self.typ, self.desc = name, typ, desc

    @property
    def box(self):
        return (self.x, self.y, self.w, self.h)

    @property
    def center(self):
        return (self.x + self.w / 2, self.y + self.h / 2)


class Diagram:
    def __init__(self, w, h, title, subtitle):
        self.w, self.h = w, h
        self.title, self.subtitle = title, subtitle
        self.back, self.front, self.labels = [], [], []

    # --- elementy C4 -------------------------------------------------------
    def el(self, kind, x, y, w, h, name, typ, desc=""):
        el = El(kind, x, y, w, h, name, typ, desc)
        fill, stroke, ink, sub = FILL[kind], STROKE[kind], INK[kind], SUB[kind]
        p = self.front
        if kind == "person":
            r = 34
            body_top = y + 2 * r - 8
            p.append(f'<rect x="{x}" y="{body_top}" width="{w}" height="{y + h - body_top}" rx="36" '
                     f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
            p.append(f'<circle cx="{x + w / 2}" cy="{y + r}" r="{r}" fill="{fill}"/>')
            top, area = body_top + 6, y + h - body_top - 6
        elif kind == "db":
            ry = 16
            p.append(f'<path d="M{x},{y + ry} L{x},{y + h - ry} A{w / 2},{ry} 0 0 0 {x + w},{y + h - ry} '
                     f'L{x + w},{y + ry} A{w / 2},{ry} 0 0 0 {x},{y + ry} Z" fill="{fill}" '
                     f'stroke="{stroke}" stroke-width="1.5"/>')
            p.append(f'<ellipse cx="{x + w / 2}" cy="{y + ry}" rx="{w / 2}" ry="{ry}" fill="{fill}" '
                     f'stroke="{stroke}" stroke-width="1.5"/>')
            top, area = y + 2 * ry, h - 2 * ry
        else:
            p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" '
                     f'stroke="{stroke}" stroke-width="1.5"/>')
            top, area = y, h
        name_l = wrap(name, w - 28, 16, 0.6)
        typ_l = wrap(typ, w - 20, 12, 0.56)
        desc_l = wrap(desc, w - 28, 12.5, 0.55) if desc else []
        block = len(name_l) * 20 + len(typ_l) * 15 + (6 + len(desc_l) * 16 if desc_l else 0)
        cy = top + (area - block) / 2
        cx = x + w / 2
        for s in name_l:
            cy += 20
            p.append(txt(cx, cy - 4, s, 16, ink, "bold"))
        for s in typ_l:
            cy += 15
            p.append(txt(cx, cy - 3, s, 12, sub))
        if desc_l:
            cy += 6
            for s in desc_l:
                cy += 16
                p.append(txt(cx, cy - 4, s, 12.5, ink))
        return el

    def boundary(self, x, y, w, h, name, typ):
        self.back.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="none" '
                         f'stroke="#8A8A8A" stroke-width="1.6" stroke-dasharray="9 6"/>')
        self.back.append(txt(x + 18, y + h - 36, name, 15, "#333", "bold", "start"))
        self.back.append(txt(x + 18, y + h - 17, typ, 12, "#666", "normal", "start"))

    # --- relacje -----------------------------------------------------------
    @staticmethod
    def _clip(box, px, py):
        x, y, w, h = box
        cx, cy = x + w / 2, y + h / 2
        dx, dy = px - cx, py - cy
        tx = (w / 2) / abs(dx) if dx else math.inf
        ty = (h / 2) / abs(dy) if dy else math.inf
        t = min(tx, ty)
        return cx + dx * t, cy + dy * t

    def rel(self, a, b, label, tech=None, sp=None, ep=None, t=0.5, off=(0, 0),
            offset=0, wrapw=210, marker="arrow", dash="7 5"):
        p1 = sp or self._clip(a.box, *b.center)
        p2 = ep or self._clip(b.box, *a.center)
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        ln = math.hypot(dx, dy)
        ux, uy = dx / ln, dy / ln
        if offset:
            nx, ny = -uy * offset, ux * offset
            p1, p2 = (p1[0] + nx, p1[1] + ny), (p2[0] + nx, p2[1] + ny)
        p1 = (p1[0] + ux * 3, p1[1] + uy * 3)
        p2 = (p2[0] - ux * 4, p2[1] - uy * 4)
        self.back.append(f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
                         f'stroke="{LINE}" stroke-width="1.7" stroke-dasharray="{dash}" '
                         f'marker-end="url(#{marker})"/>')
        if label:
            lx = p1[0] + (p2[0] - p1[0]) * t + off[0]
            ly = p1[1] + (p2[1] - p1[1]) * t + off[1]
            self.label(lx, ly, label, tech, wrapw)

    def label(self, cx, cy, label, tech=None, wrapw=210):
        lines = [(s, 12.5, "#222", "normal") for s in wrap(label, wrapw, 12.5)]
        if tech:
            lines += [(s, 11, "#666", "normal") for s in wrap(f"[{tech}]", wrapw, 11)]
        width = max(len(s) * size * 0.56 for s, size, _, _ in lines) + 14
        height = sum(size + 4 for _, size, _, _ in lines) + 8
        x0, y0 = cx - width / 2, cy - height / 2
        self.labels.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{width:.1f}" height="{height:.1f}" '
                           f'rx="4" fill="#FFFFFF" fill-opacity="0.94"/>')
        yy = y0 + 4
        for s, size, fill, weight in lines:
            yy += size + 4
            self.labels.append(txt(cx, yy - 3, s, size, fill, weight))

    # --- UML (poziom kodu) -------------------------------------------------
    def uml_class(self, x, y, w, stereo, name, attrs, methods):
        lh, head = 22, 52
        a_h = len(attrs) * lh + 14 if attrs else 12
        m_h = 0 if methods is None else (len(methods) * lh + 14 if methods else 12)
        h = head + a_h + m_h
        p = self.front
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#FFFFFF" '
                 f'stroke="#2E6295" stroke-width="1.5"/>')
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{head}" rx="4" fill="#DCEBFA" '
                 f'stroke="#2E6295" stroke-width="1.5"/>')
        p.append(txt(x + w / 2, y + 20, f"«{stereo}»", 12, "#2E4A6B", italic=True))
        p.append(txt(x + w / 2, y + 41, name, 16, "#0B2440", "bold"))
        yy = y + head
        for s in attrs:
            p.append(txt(x + 16, yy + 7 + 15, s, 13, "#1A1A1A", anchor="start", family=MONO))
            yy += lh
        yy = y + head + a_h
        if methods is not None:
            p.append(f'<line x1="{x}" y1="{yy}" x2="{x + w}" y2="{yy}" stroke="#2E6295" stroke-width="1.2"/>')
            for s in methods:
                p.append(txt(x + 16, yy + 7 + 15, s, 13, "#1A1A1A", anchor="start", family=MONO))
                yy += lh
        return El("class", x, y, w, h, name, stereo, "")

    def note(self, x, y, w, lines, title):
        h = 44 + len(lines) * 20 + 10
        f = 16
        self.front.append(f'<path d="M{x},{y} L{x + w - f},{y} L{x + w},{y + f} L{x + w},{y + h} '
                          f'L{x},{y + h} Z" fill="#FFF8DC" stroke="#B8A44C" stroke-width="1.3"/>')
        self.front.append(f'<path d="M{x + w - f},{y} L{x + w - f},{y + f} L{x + w},{y + f}" '
                          f'fill="none" stroke="#B8A44C" stroke-width="1.3"/>')
        self.front.append(txt(x + 16, y + 28, title, 13.5, "#4A3F10", "bold", "start"))
        yy = y + 44
        for s in lines:
            yy += 20
            self.front.append(txt(x + 16, yy - 4, s, 13, "#1A1A1A", anchor="start", family=MONO))

    # --- legenda i zapis ---------------------------------------------------
    def legend(self, x, y, items):
        rows = len(items)
        h = 46 + rows * 30
        self.front.append(f'<rect x="{x}" y="{y}" width="330" height="{h}" rx="8" fill="#FAFAFA" '
                          f'stroke="#D0D0D0"/>')
        self.front.append(txt(x + 16, y + 26, "Legenda", 13.5, "#333", "bold", "start"))
        yy = y + 44
        for kind, label in items:
            sx, sy = x + 16, yy
            if kind == "person":
                self.front.append(f'<rect x="{sx}" y="{sy + 7}" width="36" height="15" rx="7" fill="{FILL[kind]}"/>')
                self.front.append(f'<circle cx="{sx + 18}" cy="{sy + 4}" r="6" fill="{FILL[kind]}"/>')
            elif kind == "db":
                self.front.append(f'<path d="M{sx},{sy + 4} L{sx},{sy + 18} A18,4 0 0 0 {sx + 36},{sy + 18} '
                                  f'L{sx + 36},{sy + 4} A18,4 0 0 0 {sx},{sy + 4} Z" fill="{FILL[kind]}"/>')
                self.front.append(f'<ellipse cx="{sx + 18}" cy="{sy + 4}" rx="18" ry="4" fill="{FILL[kind]}" '
                                  f'stroke="{STROKE[kind]}"/>')
            elif kind == "boundary":
                self.front.append(f'<rect x="{sx}" y="{sy}" width="36" height="22" rx="4" fill="none" '
                                  f'stroke="#8A8A8A" stroke-width="1.4" stroke-dasharray="5 3"/>')
            elif kind == "rel":
                self.front.append(f'<line x1="{sx}" y1="{sy + 11}" x2="{sx + 32}" y2="{sy + 11}" stroke="{LINE}" '
                                  f'stroke-width="1.7" stroke-dasharray="6 4" marker-end="url(#arrow)"/>')
            else:
                self.front.append(f'<rect x="{sx}" y="{sy}" width="36" height="22" rx="4" fill="{FILL[kind]}"/>')
            self.front.append(txt(x + 64, yy + 16, label, 12.5, "#333", anchor="start"))
            yy += 30

    def save(self, name):
        defs = (
            '<defs>'
            f'<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker>'
            f'<marker id="open" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="11" markerHeight="11" '
            f'orient="auto-start-reverse"><path d="M0,0 L11,6 L0,12" fill="none" stroke="{LINE}" '
            f'stroke-width="1.6"/></marker>'
            '</defs>'
        )
        head = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'width="{self.w}" height="{self.h}" font-family="{FONT}">',
            defs,
            f'<rect width="{self.w}" height="{self.h}" fill="#FFFFFF"/>',
            txt(40, 48, self.title, 24, "#111", "bold", "start"),
            txt(40, 75, self.subtitle, 14, "#555", "normal", "start"),
        ]
        body = head + self.back + self.front + self.labels + ["</svg>"]
        (OUT / name).write_text("\n".join(body), encoding="utf-8")
        print("zapisano", OUT / name)


# ---------------------------------------------------------------------------
# Wspolne opisy
# ---------------------------------------------------------------------------
SYS = "micro:bit Arcade Ranking"
GRACZ_DESC = "Gra na micro:bicie i sprawdza ranking w przeglądarce oraz na wyświetlaczu."
D = {
    "gra": ("Gra", "[Kontener: micro:bit, MakeCode]",
            "Gra zręcznościowa. Po rozgrywce wysyła identyfikator gracza (PID) i wynik (SCORE)."),
    "bramka": ("Bramka wyników", "[Kontener: Arduino + Wi-Fi, C++]",
               "Odbiera dane z micro:bita, zamienia bity na obiekt wyniku (ID, SCORE, TIMESTAMP) "
               "i wysyła go do Web API."),
    "api": ("Web API", "[Kontener: C#, ASP.NET Core]",
            "CRUD wyników. GameController: POST AddScore zapisuje wynik, GET zwraca listę wyników."),
    "baza": ("Baza danych", "[Kontener: relacyjna baza SQL]",
             "Tabela wyników z kolumnami ID, PID, SCORE, TS."),
    "wysw": ("Wyświetlacz rankingu", "[Kontener: Arduino + OLED/LCD, C++]",
             "Pobiera ranking z Web API i pokazuje Top 10 na wyświetlaczu."),
    "www": ("Strona WWW z rankingiem", "[Kontener: JavaScript, przeglądarka]",
            "Pobiera wyniki przez fetch() i wyświetla ranking online."),
}
CW, CH = 280, 170
COLS = {"L": 100, "M": 640, "R": 1180}


# ---------------------------------------------------------------------------
# C1 - kontekst systemu
# ---------------------------------------------------------------------------
d = Diagram(1100, 640, f"[Kontekst systemu] {SYS}",
            "C4 – poziom 1. Kto korzysta z systemu i z czym system się łączy.")
gracz = d.el("person", 400, 110, 300, 200, "Gracz", "[Osoba]", GRACZ_DESC)
system = d.el("system", 330, 420, 440, 180, SYS, "[System]",
              "Gra zręcznościowa na micro:bit. Zapisuje identyfikator gracza i wynik w bazie online "
              "oraz pokazuje ranking na stronie WWW i na fizycznym wyświetlaczu.")
d.rel(gracz, system, "Gra w grę i sprawdza ranking (WWW, wyświetlacz)", wrapw=230)
d.legend(810, 460, [("person", "Osoba"), ("system", "System (w zakresie)"),
                    ("rel", "Relacja")])
d.save("c1-kontekst.svg")


# ---------------------------------------------------------------------------
# C2 - kontenery (+ wspolny uklad dla diagramu dynamicznego)
# ---------------------------------------------------------------------------
def container_layout(d):
    g = d.el("person", 630, 90, 300, 192, "Gracz", "[Osoba]", GRACZ_DESC)
    d.boundary(40, 350, 1480, 650, SYS, "[System]")
    ya, yb = 430, 750
    els = {
        "gra": d.el("container", COLS["L"], ya, CW, CH, *D["gra"]),
        "www": d.el("container", COLS["M"], ya, CW, CH, *D["www"]),
        "wysw": d.el("container", COLS["R"], ya, CW, CH, *D["wysw"]),
        "bramka": d.el("container", COLS["L"], yb, CW, CH, *D["bramka"]),
        "api": d.el("container", COLS["M"], yb, CW, CH, *D["api"]),
        "baza": d.el("db", COLS["R"], yb, CW, CH, *D["baza"]),
    }
    return g, els


d = Diagram(1560, 1040, f"[Kontenery] {SYS}",
            "C4 – poziom 2. Z jakich uruchamialnych części składa się system i jak się komunikują.")
g, c = container_layout(d)
d.rel(g, c["gra"], "Gra w grę", sp=(700, 282), ep=(320, 428), t=0.3)
d.rel(g, c["www"], "Sprawdza ranking", "HTTPS", sp=(780, 282), ep=(780, 428), t=0.36)
d.rel(g, c["wysw"], "Ogląda Top 10", sp=(860, 282), ep=(1240, 428), t=0.3)
d.rel(c["gra"], c["bramka"], "Przesyła PID i wynik", "radio / UART")
d.rel(c["bramka"], c["api"], "Wysyła wynik: POST AddScore(GUID, INT, DT)", "HTTP, JSON", wrapw=190)
d.rel(c["www"], c["api"], "Pobiera listę wyników: fetch() → GET", "HTTP, JSON")
d.rel(c["wysw"], c["api"], "Pobiera Top 10: GET", "HTTP, JSON")
d.rel(c["api"], c["baza"], "Zapisuje i odczytuje wyniki", "SQL", wrapw=190)
d.legend(1190, 40, [("person", "Osoba"), ("boundary", "Granica systemu"),
                    ("container", "Kontener"), ("db", "Kontener: baza danych"),
                    ("rel", "Relacja (strzałka od strony wywołującej)")])
d.save("c2-kontenery.svg")


# ---------------------------------------------------------------------------
# Diagram dynamiczny - kolejnosc interakcji
# ---------------------------------------------------------------------------
d = Diagram(1560, 1040, f"[Diagram dynamiczny] Zapis wyniku i odczyt rankingu",
            "C4 – widok dynamiczny. Ponumerowane kroki pokazują, jak dane przechodzą przez kontenery.")
g, c = container_layout(d)
d.rel(g, c["gra"], "1. Gra i kończy rozgrywkę", sp=(700, 282), ep=(320, 428), t=0.3)
d.rel(c["gra"], c["bramka"], "2. Wysyła PID i wynik", "radio / UART")
d.rel(c["bramka"], c["api"], "3. POST AddScore(GUID, INT, DT)", "HTTP, JSON", wrapw=190)
d.rel(c["api"], c["baza"], "4. Zapisuje wynik (INSERT)", "SQL", offset=-16, off=(0, -30), wrapw=200)
d.rel(g, c["www"], "5. Otwiera ranking", "HTTPS", sp=(780, 282), ep=(780, 428), t=0.36)
d.rel(c["www"], c["api"], "6. fetch(): GET listy wyników", "HTTP, JSON")
d.rel(c["wysw"], c["api"], "7. Cyklicznie: GET Top 10", "HTTP, JSON")
d.rel(c["api"], c["baza"], "8. Odczytuje wyniki (SELECT … ORDER BY SCORE DESC)", "SQL",
      offset=16, off=(0, 34), wrapw=200)
d.legend(1190, 40, [("person", "Osoba"), ("boundary", "Granica systemu"),
                    ("container", "Kontener"), ("db", "Kontener: baza danych"),
                    ("rel", "Krok interakcji (numer = kolejność)")])
d.save("dynamiczny.svg")


# ---------------------------------------------------------------------------
# C3 - komponenty Web API
# ---------------------------------------------------------------------------
d = Diagram(1480, 1230, "[Komponenty] Web API",
            "C4 – poziom 3. Z jakich części składa się kontener Web API.")
bram = d.el("container", 80, 110, CW, CH, *D["bramka"])
www = d.el("container", 600, 110, CW, CH, *D["www"])
wysw = d.el("container", 1120, 110, CW, CH, *D["wysw"])
d.boundary(470, 350, 540, 600, "Web API", "[Kontener: C#, ASP.NET Core]")
ctrl = d.el("component", 590, 410, 300, 190, "GameController", "[Komponent: kontroler ASP.NET Core]",
            "POST AddScore(GUID, INT, DT) – zapisuje wynik. GET – zwraca List<GameScore> jako JSON.")
repo = d.el("component", 590, 690, 300, 170, "Repozytorium wyników",
            "[Komponent: C#, Entity Framework Core]",
            "Zapis i odczyt wyników w bazie danych (operacje CRUD).")
baza = d.el("db", 600, 1020, CW, 170, *D["baza"])
d.rel(bram, ctrl, "Wysyła wynik: POST AddScore", "HTTP, JSON", t=0.45)
d.rel(www, ctrl, "fetch() → GET listy wyników", "HTTP, JSON")
d.rel(wysw, ctrl, "GET Top 10", "HTTP, JSON", t=0.45)
d.rel(ctrl, repo, "Zapisuje i pobiera wyniki")
d.rel(repo, baza, "Czyta i zapisuje", "SQL", t=0.42)
d.legend(60, 1000, [("boundary", "Granica kontenera"), ("container", "Kontener"),
                    ("db", "Kontener: baza danych"), ("component", "Komponent"),
                    ("rel", "Relacja")])
d.save("c3-web-api.svg")


# ---------------------------------------------------------------------------
# C3 - komponenty bramki (Arduino)
# ---------------------------------------------------------------------------
d = Diagram(1500, 1060, "[Komponenty] Bramka wyników (Arduino)",
            "C4 – poziom 3. Jak Arduino zamienia dane z micro:bita na żądanie HTTP.")
gra = d.el("container", 150, 110, CW, CH, *D["gra"])
d.boundary(80, 350, 1340, 400, "Bramka wyników", "[Kontener: Arduino + Wi-Fi, C++]")
odb = d.el("component", 150, 430, 260, 190, "Odbiornik danych", "[Komponent: C++, Serial / radio]",
           "Odbiera surowe bajty wysłane przez micro:bita.")
konw = d.el("component", 620, 430, 260, 190, "Konwerter bit → klasa", "[Komponent: C++]",
            "Zamienia odebrane bity na obiekt wyniku: ID (GUID), SCORE (INT), TIMESTAMP (DATETIME).")
http = d.el("component", 1090, 430, 260, 190, "Klient HTTP", "[Komponent: C++, Wi-Fi, HTTPClient]",
            "Zamienia obiekt na JSON i wysyła go do Web API.")
api = d.el("container", 1080, 840, CW, CH, *D["api"])
d.rel(gra, odb, "Przesyła PID i wynik", "radio / UART", t=0.42)
d.rel(odb, konw, "Przekazuje bajty", wrapw=170)
d.rel(konw, http, "Przekazuje obiekt wyniku", wrapw=170)
d.rel(http, api, "POST AddScore(GUID, INT, DT)", "HTTP, JSON", t=0.42)
d.legend(80, 820, [("boundary", "Granica kontenera"), ("container", "Kontener"),
                   ("component", "Komponent"), ("rel", "Relacja")])
d.save("c3-bramka.svg")


# ---------------------------------------------------------------------------
# C4 - kod (diagram klas UML dla Web API)
# ---------------------------------------------------------------------------
d = Diagram(1380, 840, "[Kod] Web API – klasy i tabela",
            "C4 – poziom 4 (diagram klas UML). Szczegóły komponentów GameController i Repozytorium wyników.")
ctl = d.uml_class(60, 120, 580, "ApiController", "GameController",
                  ["- repository: IGameScoreRepository"],
                  ["+ AddScore(pid: Guid, score: int, ts: DateTime)  [HttpPost]",
                   "+ GetScores(): List<GameScore>  [HttpGet]"])
rep = d.uml_class(60, 420, 580, "interface", "IGameScoreRepository", [],
                  ["+ Add(score: GameScore): void",
                   "+ GetAll(): List<GameScore>"])
gs = d.uml_class(860, 120, 460, "encja", "GameScore",
                 ["+ Id: Guid",
                  "+ PlayerId: Guid        // PID",
                  "+ Score: int",
                  "+ Timestamp: DateTime   // TS"], [])
tab = d.uml_class(860, 420, 460, "tabela SQL", "GameScores",
                  ["ID      uuid        PK",
                   "PID     uuid",
                   "SCORE   int",
                   "TS      timestamp"], None)
d.note(60, 620, 580, ['[',
                      '  { "id": "…", "pid": "…", "score": 120,',
                      '    "ts": "2026-10-16T12:00:00Z" },',
                      '  { … }, { … }',
                      ']'], "Odpowiedź GET (JSON) – lista obiektów GameScore")
d.rel(ctl, rep, "używa", sp=(350, ctl.y + ctl.h), ep=(350, rep.y), marker="open", wrapw=120)
d.rel(ctl, gs, "tworzy i zwraca", sp=(ctl.x + ctl.w, 190), ep=(gs.x, 190), marker="open", wrapw=140)
d.rel(rep, gs, "zapisuje i odczytuje", sp=(rep.x + rep.w, rep.y + 50), ep=(gs.x + 40, gs.y + gs.h),
      marker="open", wrapw=140)
d.rel(gs, tab, "mapowanie ORM", sp=(1090, gs.y + gs.h), ep=(1090, tab.y), marker="open", wrapw=140)
d.save("c4-kod.svg")

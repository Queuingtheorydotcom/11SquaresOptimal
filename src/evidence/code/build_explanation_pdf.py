"""Render the explanatory report. Final mode requires global acceptance."""
from pathlib import Path
from fractions import Fraction
import argparse
import hashlib
import json
import math
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.pagesizes import A4

BASE=Path(__file__).resolve().parents[1]
INK=colors.HexColor('#172B3A');BLUE=colors.HexColor('#196887')
MUTED=colors.HexColor('#5D6F7A');LIGHT=colors.HexColor('#EAF2F5')
GOLD=colors.HexColor('#DCA644');LINE=colors.HexColor('#D6E1E6')
W,H=A4;LEFT=51;WIDTH=W-102
STYLES={
 'body':ParagraphStyle('body',fontName='Helvetica',fontSize=10.5,leading=15,textColor=INK,spaceAfter=9),
 'small':ParagraphStyle('small',fontName='Helvetica',fontSize=8.6,leading=12,textColor=MUTED),
 'formula':ParagraphStyle('formula',fontName='Courier',fontSize=9.7,leading=15,textColor=INK),
 'heading':ParagraphStyle('heading',fontName='Helvetica-Bold',fontSize=14,leading=19,textColor=BLUE),
 'cell':ParagraphStyle('cell',fontName='Helvetica',fontSize=9.2,leading=13,textColor=INK),
}

def witness():
    # Illustration only. Exact algebraic verification is a separate proof input.
    def f(u):return ((((((((5*u-10)*u-2)*u+14)*u+12)*u-6)*u+2)*u+2)*u-1)
    lo,hi=.36,.37
    for _ in range(64):
        mid=(lo+hi)/2
        if f(mid)>0:hi=mid
        else:lo=mid
    u=(lo+hi)/2;c=(1-u*u)/(1+u*u);s=2*u/(1+u*u)
    T=(6*u+4)/(1+2*u-u*u)
    r=1-(T-3)*c;a=((1+r)*c-1)/s;v=c-s
    w=(T-1)/s-r-(3+a)*c/s;x=1+2/c-(T-2)*s/c
    unit=((0,0),(1,0),(1,1),(0,1))
    squares=[[(ox+dx,oy+dy) for dx,dy in unit] for ox,oy in
             [(0,0),(T-1,0),(x,T-1),(0,T-1),(1,T-1),(0,T-2)]]
    for ox,oy in [(0,0),(a,-1),(1,v),(a+1,v-1),(a+2,-w)]:
        squares.append([(1+c*(ox+dx)-s*(oy+dy-r),1+s*(ox+dx)+c*(oy+dy-r)) for dx,dy in unit])
    return squares,T

class Report:
    def __init__(self,path,draft,receipt):
        self.c=canvas.Canvas(str(path),pagesize=A4,pageCompression=1)
        self.c.setTitle('Eleven unit squares: exact endpoint and computational proof')
        self.c.setAuthor('Eleven-square verification project')
        self.draft=draft;self.receipt=receipt;self.page=0;self.y=0
    def new(self,number,title):
        if self.page:self.c.showPage()
        self.page+=1;self.y=H-78
        self.c.setFillColor(BLUE);self.c.setFont('Helvetica-Bold',8.5)
        self.c.drawString(LEFT,H-36,'ELEVEN SQUARES / VERIFICATION REPORT')
        self.c.setFillColor(MUTED);self.c.setFont('Helvetica',8)
        self.c.drawRightString(W-LEFT,H-36,'27 September 2026')
        self.c.setStrokeColor(LINE);self.c.line(LEFT,45,W-LEFT,45)
        self.c.setFont('Helvetica',8);self.c.setFillColor(MUTED)
        label='DRAFT - global acceptance pending' if self.draft else 'Exact computational certificate proof'
        self.c.drawString(LEFT,31,label);self.c.drawRightString(W-LEFT,31,str(self.page))
        self.c.setFont('Helvetica-Bold',25);self.c.setFillColor(INK)
        self.c.drawString(LEFT,self.y,f'{number}  {title}');self.y-=29
    def p(self,text,style='body',space=10):
        p=Paragraph(text,STYLES[style]);_,h=p.wrap(WIDTH,1000)
        if self.y-h<61:raise RuntimeError(f'Page {self.page} overflow at: {text[:80]}')
        p.drawOn(self.c,LEFT,self.y-h);self.y-=h+space
    def formula(self,text):self.p(escape(text).replace('\n','<br/>'),'formula',13)
    def heading(self,text):self.y-=5;self.p(text,'heading',8)
    def table(self,rows,widths):
        wrapped=[[Paragraph(str(x),STYLES['cell']) for x in row] for row in rows]
        t=Table(wrapped,colWidths=widths,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('LINEBELOW',(0,0),(-1,0),.7,LINE),
                              ('LINEBELOW',(0,1),(-1,-1),.4,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),
                              ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
                              ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
        _,h=t.wrap(WIDTH,1000)
        if self.y-h<61:raise RuntimeError(f'Table overflow on page {self.page}')
        t.drawOn(self.c,LEFT,self.y-h);self.y-=h+15
    def packing(self,size=258):
        squares,T=witness();x=LEFT+(WIDTH-size)/2;y=self.y-size-5;scale=size/T
        for i,S in enumerate(squares):
            path=self.c.beginPath();path.moveTo(x+S[0][0]*scale,y+S[0][1]*scale)
            for px,py in S[1:]:path.lineTo(x+px*scale,y+py*scale)
            path.close();self.c.setFillColor(LIGHT if i<6 else colors.HexColor('#F6E3B9'))
            self.c.setStrokeColor(BLUE if i<6 else colors.HexColor('#A27322'));self.c.setLineWidth(.8)
            self.c.drawPath(path,stroke=1,fill=1)
            self.c.setFillColor(INK);self.c.setFont('Helvetica-Bold',9)
            self.c.drawCentredString(x+sum(p[0] for p in S)*scale/4,y+sum(p[1] for p in S)*scale/4-3,str(i))
        self.c.setStrokeColor(INK);self.c.setLineWidth(1.4);self.c.rect(x,y,size,size)
        self.c.setFont('Helvetica-Oblique',11);self.c.drawCentredString(x+size/2,y-16,'T')
        self.y=y-29
    def finish(self):self.c.save()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--draft',action='store_true');a=ap.parse_args()
    receipt_path=BASE/'results/GLOBAL_PROOF.json'
    receipt=json.loads(receipt_path.read_text()) if receipt_path.is_file() else None
    if not a.draft:
        assert receipt and receipt['status']=='PASS_COMPLETE_ELEVEN_SQUARE_OPTIMALITY'
        assert receipt['global_optimality_proved'] is True
    out=BASE/'output/pdf';out.mkdir(parents=True,exist_ok=True)
    path=out/('eleven-square-proof-draft.pdf' if a.draft else 'eleven-square-optimality.pdf')
    r=Report(path,a.draft,receipt)
    r.new('1','The exact endpoint')
    r.p('Eleven independently rotated unit squares are packed in a square container. Interiors may not overlap; boundary contact is allowed. The target is the smallest possible container side.')
    r.p('<b>Result after complete certificate acceptance:</b> Walter Trump\'s known packing attains the minimum side <i>T</i>. The diagram below is illustrative; the proof uses exact algebraic coordinates.')
    r.formula('T = (6u + 4)/(1 + 2u - u^2)\nT = 3.8770835900228141773078970601...')
    r.p('Here <i>u</i> is the unique real root in (9/25, 37/100) of the following polynomial. This isolating interval specifies the endpoint exactly.')
    r.formula('5u^8 - 10u^7 - 2u^6 + 14u^5 + 12u^4\n     - 6u^3 + 2u^2 + 2u - 1 = 0')
    r.packing(248)
    r.p('Six squares are axis aligned; five share a tilted orientation. Labels agree with the exact construction source. The drawing uses rounded coordinates only.','small')
    r.p('The proof combines a finite exclusion of all other center-cell patterns with a complete capture of the surviving packing. A numerical search alone would not establish this result.','small')

    r.new('2','From geometry to 2,184 cases')
    r.p('Every hypothetical packing of side <i>S</i> &lt; <i>T</i> is placed concentrically in the slightly larger rational square of side <i>U</i>. Its unit squares are unchanged.')
    r.formula('U = 387708359002281417731 / 10^20 > T\nL = 191/50,   B = L/U')
    r.p('After multiplying coordinates by <i>B</i>, the geometry lies in the fixed field square [0,L]<super>2</super>. A rational cover divides the legal center region into 16 closed cells. Exact squared-diameter bounds show that each cell can contain at most one center: two unit squares with centers less than one unit apart overlap through their inscribed disks.')
    r.p('Choose a containing cell for each center, including any valid choice on shared boundaries. The eleven labels are distinct. There are 4,368 eleven-cell subsets. A physical half-turn maps label <i>j</i> to 15 - <i>j</i> and reduces these to 2,184 canonical cases. All case indices in this package are zero based.')
    r.table([['Proof family','Canonical cases'],['Original independently replayed baseline','1,931'],['Subsequent source-bound extensions','76'],['Returned case certificates, freshly replayed','173'],['Total excluded at the rational cap U','2,180'],['Surviving candidate cases','438, 999, 1462, 1659']], [WIDTH*.70,WIDTH*.30])
    r.p('The final verifier checks the exact case sets, their disjointness, and every dependency. Adding the counts is insufficient: a duplicated, conditional, or absent case would leave a gap.')
    r.heading('Closed boundaries are part of the problem')
    r.p('No tie-breaking convention discards a boundary packing. Each exclusion applies to its closed-cell antecedent. This lets the symmetry argument reason about any valid cell assignment in any image of the packing.')

    r.new('3','Checking continuous geometry')
    r.p('The certificates describe a finite induction on exact polygons and closed orientation intervals. They are not a grid of sampled configurations. Every possible rotation of a square is represented, modulo a quarter-turn, by the closed interval 0 &lt;= <i>t</i> &lt;= 1:')
    r.formula('t = tan(theta/2)\ncos(theta) = (1-t^2)/(1+t^2)\nsin(theta) = 2t/(1+t^2)')
    r.heading('Two invariants carry the proof')
    r.p('<b>Inner ownership:</b> a certified convex hull lies strictly inside its assigned square for every pose still possible. <b>Outer containment:</b> closed center polygons and angular intervals contain every pose still possible. Both invariants begin with independently checked cell and wall geometry.')
    r.p('A strict interior core of one square cannot meet another square\'s owned hull. Exact Minkowski sums therefore forbid certain center regions. Additional collision cuts are accepted only when they are proved for the whole partner-pose cover. Necessary wall and ownership cuts may tighten the outer domains.')
    r.p('The checker reconstructs polygon arrangements with rational arithmetic. It proves that each old domain is covered by forbidden regions and retained residual regions. Point and segment domains receive separate exact coverage checks. For a two-dimensional domain, closedness fills the vertical-slab boundaries after dense interior coverage has been established.')
    r.p('A new owned hull is promoted only after every closed angular interval has been covered. Exact convex combinations justify its vertices. Branch assumptions persist through the complete source ancestry; an unconditional result requires an empty final assumption list or a separately proved discharge.')
    r.heading('Why a terminal contradiction is decisive')
    r.p('Either an owner has no surviving pose over its full allowed orientation range, or two hulls known to lie strictly inside different squares intersect. Each outcome contradicts a feasible packing. Strict interior containment is what makes forbidden-region boundaries safe without banning legal touching between the unit squares.')
    r.p('All 173 returned cases use the frozen independent v9 checker. Source hashes identify the exact traces, seeds, helpers, and cover; mathematical acceptance comes from executing the proof rules on those bytes.','small')

    r.new('4','Symmetry reduces four cases to one')
    r.p('The cell cover is preserved by a half-turn, but a quarter-turn or reflection need not permute its cells. The proof therefore constructs the common closed refinement of four square-symmetry views.')
    r.formula('(x,y),   (1-x,y),   (1-y,x),   (y,x)')
    r.p('Together with their half-turns these represent all eight square symmetries. Exact polygon intersection gives 220 nonempty refinement regions, including eight singleton points. Keeping those points is necessary for boundary cases.')
    r.p('For 1,572 pairs of regions, an exact maximum over their vertex pairs shows that their physical center distance is strictly less than one. Such a pair cannot hold two different square centers. Equality at one is retained.')
    r.p('Assume every view avoids case438. Then its mask must be one of the other three candidates or their half-turn images. An exhaustive finite relaxation assigns one refinement region per occupied cell, enforces distinct labels in each view, and applies all strict distance bans.')
    r.table([['Starting canonical case','Independent search result','Search nodes'],['999','Impossible','75'],['1462','Impossible','61'],['1659','Impossible','31']], [WIDTH*.39,WIDTH*.38,WIDTH*.23])
    r.p('A genuine packing whose every image avoided case438 would supply a solution to this finite relaxation. The exact search proves that no such solution exists. Consequently some square-symmetry image admits the precise closed-cell assignment of case438.')
    r.heading('The role of boundary choices')
    r.p('Containing labels may be chosen independently in the four views. Their intersection contains the actual center, so it is one of the retained closed regions. The proof requires neither a symmetry-compatible tie-break nor a claim that the cover has every square symmetry.')
    r.p('This lemma becomes global only after all 2,180 noncandidate exclusions have been accepted. It does not supply those exclusions itself.','small')

    r.new('5','Capturing the surviving packing')
    r.p('For case438, a complete closed partition separates three impossible branches from one small surviving pose region. Here <i>y</i><sub>15</sub> is the centered physical vertical coordinate of the square in cell15, and the <i>t</i> values are half-angle parameters.')
    r.table([['Closed branch','Accepted conclusion'],['y15 &lt;= 5/4','Contradiction'],['y15 &gt;= 5/4 and t13 &lt;= 147/512','Contradiction'],['y15 &gt;= 5/4, t13 &gt;= 147/512,<br/>t2 &lt;= 183/512','Contradiction'],['y15 &gt;= 5/4, t13 &gt;= 147/512,<br/>t2 &gt;= 183/512','Inside the proved local rectangle']], [WIDTH*.70,WIDTH*.30])
    r.p('The branches overlap at equality and cover every possibility. In the last branch, 136 live orientation rows and 1,542 center vertices are enclosed in the local rectangle. Convexity covers every point in each center polygon; exact angular estimates cover each entire interval, including the quarter-turn seam.')
    r.heading('The rational cap is not the exact endpoint')
    r.p('The exclusion calculations use <i>U</i>, while local isolation holds in the exact fixed container [0,T]<super>2</super>. For a field center <i>p</i>, the local center is obtained by the exact map below, with Q(x,y) = (-y,x):')
    r.formula('z_center = Q^(-1)(p/B - (U/2,U/2))\n           + (T/2,T/2)')
    r.p('This retains the small but nonzero U - T translation. A packing originally centered in a container of side <i>S</i> &lt;= <i>T</i> is mapped into [0,T]<super>2</super> by a rigid change of frame. The local theorem therefore applies to precisely the coordinates enclosed by the capture certificate.')
    r.p('The conclusion concerns actual sides S &lt;= T. It does not assert that case438 is impossible at U, where small perturbations can be feasible.','small')

    r.new('6','Why the local rectangle is isolated')
    r.p('Use 33 perturbation coordinates: two center displacements and one angle in radians for each of the eleven labelled squares. Exact contact analysis gives 512 raw branches and 128 distinct derivative matrices. The calculation also excludes 88 unavailable separating features throughout the rectangle.')
    r.p('Let the positive coordinate radii be r<sub>0</sub>,...,r<sub>32</sub>. They lie within the analytic working box of radius 1/64. This rectangle need not fit inside the older uniform isolation radius 1/248; its directional curvature bounds are checked separately.')
    r.p('For each derivative row, an exact rational upper bound K<sub>i</sub> controls the second-order remainder. For each branch and each signed coordinate, a nonnegative rational vector gives a dual certificate. There are 128 x 33 x 2 = 8,448 such checks.')
    r.formula('||lambda^T A - sigma e_j^T||_1 <= epsilon_j\nM_j = sum_i lambda_i K_i,   R = max_k r_k\nM_j < 2(r_j - epsilon_j R)')
    r.p('The largest certified ratio in the last inequality is approximately 0.6765052083, strictly below one. This decimal is descriptive; acceptance uses exact fractions.')
    r.heading('A short contradiction proves isolation')
    r.p('Suppose a nonzero feasible perturbation <i>h</i> lies in the closed rectangle. Normalize its size by the coordinate radii:')
    r.formula('tau = max_j |h_j|/r_j,   0 < tau <= 1')
    r.p('Choose a saturated coordinate and the dual sign opposite its displacement. Taylor\'s theorem and the necessary contact inequalities give:')
    r.formula('tau r_j <= epsilon_j tau R + tau^2 M_j/2\n        < epsilon_j tau R\n          + tau^2 (r_j - epsilon_j R)\n        <= tau r_j')
    r.p('This is impossible. Thus the only feasible pose in the closed rectangle is the exact construction. Separate strict Taylor bounds keep all 88 unavailable separation features unavailable, ensuring that every nearby feasible packing selects one of the checked branches.')
    r.p('The detailed derivative, curvature, feature, and exact-algebra arguments are in docs/PROOF.md and the preserved local theorem sources. The finite dual vectors and their independent checker are part of the proof data.','small')

    r.new('7','The global conclusion and verification')
    r.p('<b>Assume a packing exists at a side S &lt; T.</b> Place it concentrically in the rational-cap square. The complete case union leaves only the four candidate patterns. The exact symmetry lemma puts some image in case438. The complete capture then puts it in the proved local rectangle in [0,T]<super>2</super>.')
    r.p('Local isolation forces this image to equal the exact known construction. That construction has span T in both coordinate directions, so it cannot fit in the original side-S container. This contradiction excludes every S &lt; T. The exact construction supplies feasibility at T, giving the claimed optimum.')
    r.heading('What the proof package contains')
    r.p('The directory contains the original compressed inputs, the frozen geometric and algebraic checkers, complete source ancestry, explicit path-relocation adapters, fresh and historical replay receipts, and Markdown explaining every implication. It preserves old evidence bytes and records new execution separately.')
    r.p('The recorded-proof command validates source bindings and composes the accepted results. The full-replay command recomputes the geometry and algebra from the supplied proof objects. Exact commands and runtime dependencies appear in the package README; running a metadata check is not the same operation as replaying geometry.')
    r.heading('Scope and trust')
    r.p('This is a computational certificate proof based on reviewed mathematical reductions, exact integer/rational and algebraic arithmetic, the supplied checker source and dependencies, and the computing system executing them. It is not a development in a formal proof assistant. Neither a search heuristic nor an LLM\'s assertion is used as an acceptance rule. No claim of historical priority is made.')
    r.heading('Provenance and further detail')
    r.p('The preserved jlevy/squares construction attributes the packing to Walter Trump and its geometric reconstruction to David Ellsworth. Upstream revision c55726e1e885227f63110131c0a914665175ff89 provides the exact construction and local mathematics. Its local theorem alone makes no global claim.','small')
    r.p('<link href="https://github.com/jlevy/squares/blob/main/packing/cases/trump11/isolation-theorem.md" color="#196887">Upstream local theorem</link> &nbsp;|&nbsp; <link href="https://www.kurims.kyoto-u.ac.jp/EMIS/journals/EJC/Volume_10/PDF/v10i1r8.pdf" color="#196887">Stromquist, Packing 10 or 11 Unit Squares in a Square (2003)</link>','small')
    if a.draft:
        r.p('<b>Draft status:</b> this report does not yet assert completed global acceptance. Outstanding computations and their exact conditions are recorded in docs/PROOF.md.','small')
    else:
        digest=hashlib.sha256(receipt_path.read_bytes()).hexdigest()
        r.p('Accepted global receipt: results/GLOBAL_PROOF.json. SHA-256:','small',3)
        r.formula(digest[:32]+'\n'+digest[32:])
    r.finish();print(path)

if __name__=='__main__':main()

import pygame
import math
from src.quest_system import DIFFICULTY_STARS, DIFFICULTY_COL, QuestManager


def _lerp_col(a, b, t):
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))


# ---------------------------------------------------------------------------
# Notice Board Scene — shown when pressing E at market area
# (or called from town scene for the inn rumour board)
# ---------------------------------------------------------------------------

class NoticeBoardScene:
    """
    Full-screen notice board with:
    - Available quests to accept (up to 4)
    - Wanted posters for bosses
    - Town notices / flavour text
    Tabs: QUESTS | WANTED | NOTICES
    """

    TOWN_NOTICES = [
        ("Inn Special",       "Rest at the Rusty Flagon — restored\nHP and rumours included. Borin's treat."),
        ("Dungeon Warning",   "Adventurers are advised to stock\npotions before entering. Many don't return."),
        ("Lost: One Cat",     "Grey tabby, answers to 'Mochi'.\nLast seen near the dungeon gate.\nReward: 5 gold."),
        ("Market Day",        "Fresh supplies arriving Thursday.\nGorin's Forge has iron stock.\nMira's Sundries — restocked."),
        ("Curfew Notice",     "By order of the Town Guard: no\ncitizens near the dungeon after dusk.\nViolators will be escorted home."),
        ("Adventurers Guild", "Seeking capable fighters.\nAll quest rewards have been doubled\nthis season. Enquire at the board."),
        ("Strange Lights",    "Residents report blue lights\nemanating from the lower dungeon.\nDo not investigate alone."),
        ("Reward Offered",    "For information leading to the\nrecovery of Aldric's stolen grain.\nSpeak to the miller's house."),
    ]

    WANTED_BOSSES = [
        ("goblin_king",      "GOBLIN KING",     150, (80,148,60),
         "Rules the dungeon depths.\nCrown made from adventurer bones.\nExtremely dangerous."),
        ("bone_lord",        "BONE LORD",        180, (220,215,195),
         "Ancient armoured skeleton.\nKnown to resurrect itself.\nDestroy completely."),
        ("mountain_king",    "MOUNTAIN KING",    200, (100,145,90),
         "Cave troll of enormous size.\nThrows boulders. Regenerates.\nApproach with extreme caution."),
        ("archmage",         "ARCHMAGE",         190, (140,70,220),
         "Corrupted wizard. Casts fire,\nice and lightning. Very dangerous.\nBring fire resistance if possible."),
        ("inferno_duke",     "INFERNO DUKE",     195, (220,60,20),
         "Winged demon lord. Wreathed in\npermanent fire. Burns everything.\nDo NOT engage near flammables."),
        ("rat_king",         "RAT KING",         170, (150,125,90),
         "Mass of fused rats wearing a crown.\nCommands rat swarms. Steals items.\nSeal your pockets."),
        ("warchief_grommak", "WARCHIEF GROMMAK", 210, (85,130,60),
         "Orc chieftain in full plate.\nEnrages permanently in combat.\nDo not let the fight drag out."),
        ("ancient_colossus", "ANCIENT COLOSSUS", 220, (155,150,138),
         "Stone titan from a forgotten age.\nNearly immune to normal weapons.\nStrike hard and fast."),
        ("the_alpha",        "THE ALPHA",        205, (130,100,70),
         "Werewolf pack leader. Transforms\nmid-fight. Heals itself. Fast.\nSilver weapons recommended."),
        ("lich_king",        "LICH KING",        250, (130,90,210),
         "Supreme undead ruler.\nPhylactery must be destroyed first.\nMost dangerous entity known."),
    ]

    def __init__(self, screen, quest_manager: QuestManager, game_state=None):
        self.screen       = screen
        self.W, self.H    = screen.get_size()
        self.clock        = pygame.time.Clock()
        self.time         = 0.0
        self.qm           = quest_manager
        self.game_state   = game_state

        self.font_title  = pygame.font.SysFont("courier new", 26, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 16, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 13)
        self.font_tiny   = pygame.font.SysFont("courier new", 11)

        self.tab       = 0   # 0=quests, 1=wanted, 2=notices
        self.selected  = 0
        self._hover    = [0.0]*3
        self.open_anim = 0.0
        self.OPEN_DUR  = 0.35
        self._msg      = ""
        self._msg_t    = 0.0

    # ------------------------------------------------------------------ #

    def _draw_bg(self):
        for y in range(self.H):
            t = y/self.H
            pygame.draw.line(self.screen,
                             (int(10+12*t),int(7+8*t),int(4+5*t)),
                             (0,y),(self.W,y))

    def _draw_panel(self, ease):
        pw=int(self.W*0.90); ph=int(self.H*0.88)
        px=self.W//2-pw//2; py=self.H//2-ph//2
        w2=int(pw*ease); h2=int(ph*ease)
        x=self.W//2-w2//2; y=self.H//2-h2//2
        if w2 < 4: return px,py,pw,ph
        bg=pygame.Surface((w2,h2),pygame.SRCALPHA)
        bg.fill((14,10,6,248))
        self.screen.blit(bg,(x,y))
        pygame.draw.rect(self.screen,(130,100,48),(x,y,w2,h2),2)
        pygame.draw.rect(self.screen,(80,60,28),(x+5,y+5,w2-10,h2-10),1)
        sz=14
        for bx,by,dx,dy in [(x,y,1,1),(x+w2,y,-1,1),(x,y+h2,1,-1),(x+w2,y+h2,-1,-1)]:
            pygame.draw.line(self.screen,(180,145,65),(bx,by),(bx+dx*sz,by),2)
            pygame.draw.line(self.screen,(180,145,65),(bx,by),(bx,by+dy*sz),2)
        return px,py,pw,ph

    def _draw_tabs(self, px, py, pw, ease):
        tabs=["QUESTS","WANTED","NOTICES"]
        tw=pw//3
        for i,label in enumerate(tabs):
            tx=px+i*tw; ty=py+38
            is_sel=(i==self.tab)
            t=self._hover[i]
            bg=pygame.Surface((tw-4,32),pygame.SRCALPHA)
            if is_sel:
                bg.fill((35,25,12,230))
            else:
                bg.fill((int(18+20*t),int(12+14*t),int(8+8*t),180))
            self.screen.blit(bg,(tx+2,ty))
            bc=(180,145,65) if is_sel else _lerp_col((55,42,22),(130,100,45),t)
            pygame.draw.rect(self.screen,bc,(tx+2,ty,tw-4,32),2 if is_sel else 1)
            ls=self.font_medium.render(label,True,
                                       (220,190,120) if is_sel else _lerp_col((100,78,38),(180,148,75),t))
            self.screen.blit(ls,(tx+tw//2-ls.get_width()//2,ty+7))
        # Underline selected
        pygame.draw.line(self.screen,(180,145,65),
                         (px+self.tab*tw+2,py+70),(px+(self.tab+1)*tw-2,py+70),2)

    def _draw_quests_tab(self, px, py, pw, ph):
        available = self.qm.get_available()
        active_ids = {q["id"] for q in self.qm.active}
        slots_left = self.qm.MAX_ACTIVE - len(self.qm.active)

        # Header
        sl=self.font_small.render(
            f"Active: {len(self.qm.active)}/{self.qm.MAX_ACTIVE}    "
            f"Slots remaining: {slots_left}",
            True,(140,110,55))
        self.screen.blit(sl,(px+16,py+78))

        if not available:
            ns=self.font_medium.render("No quests available — check back later.",
                                        True,(80,62,30))
            self.screen.blit(ns,(px+pw//2-ns.get_width()//2,py+ph//2))
            return

        row_h=95; row_w=pw-32; start_y=py+98
        mouse=pygame.mouse.get_pos()
        for i,q in enumerate(available[:4]):
            ry=start_y+i*row_h
            is_sel=(i==self.selected)
            hov=pygame.Rect(px+16,ry,row_w,row_h-6).collidepoint(mouse)
            t=1.0 if (is_sel or hov) else 0.0
            already=q["id"] in active_ids
            can=slots_left>0 and not already

            bg=pygame.Surface((row_w,row_h-6),pygame.SRCALPHA)
            bg.fill((int(22+22*t),int(15+15*t),int(9+9*t),220))
            self.screen.blit(bg,(px+16,ry))
            bc=_lerp_col((55,42,22),(160,128,55),t) if can else (35,26,14)
            pygame.draw.rect(self.screen,bc,(px+16,ry,row_w,row_h-6),2 if is_sel else 1)

            # Difficulty stars
            diff_col=DIFFICULTY_COL.get(q["difficulty"],(150,150,150))
            ds=self.font_tiny.render(DIFFICULTY_STARS[q["difficulty"]],True,diff_col)
            self.screen.blit(ds,(px+20,ry+4))

            # Title
            tc=(225,195,130) if can else (100,78,40)
            ts=self.font_medium.render(q["title"],True,tc)
            self.screen.blit(ts,(px+20,ry+18))

            # Description
            desc_s=self.font_tiny.render(q["desc"],True,(140,110,58))
            self.screen.blit(desc_s,(px+20,ry+36))

            # Flavour
            flav_s=self.font_tiny.render(f'"{q["flavour"]}"',True,(90,70,35))
            self.screen.blit(flav_s,(px+20,ry+50))

            # Rewards
            rew=f"Reward: {q['reward_gold']}g  +{q['reward_exp']} EXP"
            if q["reward_item"]:
                rew += f"  +{q['reward_item'].replace('Item','')}"
            rs=self.font_tiny.render(rew,True,(180,160,80))
            self.screen.blit(rs,(px+20,ry+64))

            # Accept button / status
            if already:
                st=self.font_tiny.render("[ ACTIVE ]",True,(80,160,80))
                self.screen.blit(st,(px+row_w-st.get_width()-8,ry+34))
            elif can:
                ab=self.font_small.render("[ ENTER ] Accept",True,
                                           _lerp_col((100,80,35),(200,170,80),t))
                self.screen.blit(ab,(px+row_w-ab.get_width()-8,ry+34))
            else:
                st=self.font_tiny.render("[ FULL ]",True,(120,70,40))
                self.screen.blit(st,(px+row_w-st.get_width()-8,ry+34))

            if is_sel:
                arr=self.font_small.render("▶",True,(180,148,60))
                self.screen.blit(arr,(px+4,ry+row_h//2-arr.get_height()//2))

        hint=self.font_tiny.render("↑ ↓  select    ENTER  accept    ESC  back",
                                    True,(70,54,28))
        self.screen.blit(hint,(self.W//2-hint.get_width()//2,py+ph-hint.get_height()-10))

    def _draw_wanted_tab(self, px, py, pw, ph):
        completed = set(self.qm.completed)
        bosses = self.WANTED_BOSSES
        col_w=(pw-32)//2; row_h=130; start_y=py+80
        for i,(bid,bname,bounty,bcol,bdesc) in enumerate(bosses):
            cx=px+16+(i%2)*col_w
            ry=start_y+(i//2)*row_h
            killed=any(q["target"]==bid and q["type"]=="kill_boss"
                       for q in [{"target":bid,"type":"kill_boss"}]
                       if bid in completed)

            bg=pygame.Surface((col_w-8,row_h-8),pygame.SRCALPHA)
            bg.fill((22,15,9,210))
            self.screen.blit(bg,(cx,ry))
            pygame.draw.rect(self.screen,bcol,(cx,ry,col_w-8,row_h-8),2)

            # Portrait placeholder — coloured circle with initial
            pr=28
            pygame.draw.circle(self.screen,bcol,(cx+pr+8,ry+row_h//2-12),pr)
            pygame.draw.circle(self.screen,tuple(max(0,c-60) for c in bcol),
                               (cx+pr+8,ry+row_h//2-12),pr,2)
            init=self.font_medium.render(bname[0],True,(255,255,255))
            self.screen.blit(init,(cx+pr+8-init.get_width()//2,
                                   ry+row_h//2-12-init.get_height()//2))

            # WANTED header
            wh=self.font_tiny.render("— WANTED —",True,(200,60,40))
            self.screen.blit(wh,(cx+pr*2+20,ry+4))
            # Name
            ns=self.font_medium.render(bname,True,bcol)
            self.screen.blit(ns,(cx+pr*2+20,ry+16))
            # Desc lines
            for li,line in enumerate(bdesc.split("\n")[:3]):
                ls=self.font_tiny.render(line,True,(140,110,55))
                self.screen.blit(ls,(cx+pr*2+20,ry+34+li*12))
            # Bounty
            bs=self.font_small.render(f"Bounty: {bounty}g",True,(220,185,50))
            self.screen.blit(bs,(cx+pr*2+20,ry+row_h-26))

            # Deceased stamp
            if killed:
                stamp=self.font_large.render("SLAIN",True,(180,40,40))
                stamp.set_alpha(160)
                self.screen.blit(stamp,(cx+col_w//2-stamp.get_width()//2,
                                        ry+row_h//2-stamp.get_height()//2))

    def _draw_notices_tab(self, px, py, pw, ph):
        col_w=(pw-40)//2; row_h=105; start_y=py+80
        for i,(title,body) in enumerate(self.TOWN_NOTICES):
            cx=px+16+(i%2)*col_w
            ry=start_y+(i//2)*row_h

            bg=pygame.Surface((col_w-8,row_h-8),pygame.SRCALPHA)
            bg.fill((20,14,8,215))
            self.screen.blit(bg,(cx,ry))
            pygame.draw.rect(self.screen,(110,88,45),(cx,ry,col_w-8,row_h-8),1)
            # Pin
            pygame.draw.circle(self.screen,(180,55,45),(cx+col_w//2-4,ry),5)

            ts=self.font_medium.render(title,True,(215,185,110))
            self.screen.blit(ts,(cx+8,ry+10))
            pygame.draw.line(self.screen,(90,70,35),(cx+6,ry+28),(cx+col_w-14,ry+28),1)
            for li,line in enumerate(body.split("\n")[:4]):
                ls=self.font_tiny.render(line,True,(155,130,80))
                self.screen.blit(ls,(cx+8,ry+32+li*14))

    def _draw_message(self):
        if not self._msg or self._msg_t<=0: return
        alpha=min(1.0,self._msg_t/0.4)
        good="Accept" in self._msg or "accepted" in self._msg.lower()
        col=(120,200,120) if good else (200,100,80)
        ms=self.font_small.render(self._msg,True,col)
        bg=pygame.Surface((ms.get_width()+20,ms.get_height()+8),pygame.SRCALPHA)
        bg.fill((10,7,4,int(210*alpha)))
        bx=self.W//2-bg.get_width()//2; by=self.H-50
        self.screen.blit(bg,(bx,by))
        pygame.draw.rect(self.screen,col,(bx,by,bg.get_width(),bg.get_height()),1)
        ms.set_alpha(int(255*alpha))
        self.screen.blit(ms,(bx+10,by+4))

    # ------------------------------------------------------------------ #

    def run(self) -> str:
        available_quests = self.qm.get_available()
        while True:
            dt=self.clock.tick(60)/1000.0
            self.time+=dt
            self.open_anim=min(self.open_anim+dt,self.OPEN_DUR)
            ease=1-(1-min(1.0,self.open_anim/self.OPEN_DUR))**3
            self._msg_t=max(0.0,self._msg_t-dt)
            mouse=pygame.mouse.get_pos()

            # Tab hover
            for i in range(3):
                px2=self.W//2-int(self.W*0.90)//2+i*(int(self.W*0.90)//3)
                tgt=1.0 if pygame.Rect(px2+2,self.H//2-int(self.H*0.88)//2+38,
                                        int(self.W*0.90)//3-4,32).collidepoint(mouse) else 0.0
                self._hover[i]+=(tgt-self._hover[i])*10*dt
                self._hover[i]=max(0.0,min(1.0,self._hover[i]))

            for event in pygame.event.get():
                if event.type==pygame.QUIT: return "exit"
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE: return "back"
                    if event.key==pygame.K_q:
                        result = QuestLogScene(self.screen, self.qm).run()
                        if result == "exit": return "exit"
                    if event.key==pygame.K_LEFT:
                        self.tab=max(0,self.tab-1); self.selected=0
                    if event.key==pygame.K_RIGHT:
                        self.tab=min(2,self.tab+1); self.selected=0
                    if event.key==pygame.K_UP and self.tab==0:
                        self.selected=max(0,self.selected-1)
                    if event.key==pygame.K_DOWN and self.tab==0:
                        self.selected=min(len(available_quests)-1,self.selected)
                        self.selected=min(3,self.selected+1)
                    if event.key in (pygame.K_RETURN,pygame.K_SPACE) and self.tab==0:
                        if available_quests and self.selected<len(available_quests):
                            q=available_quests[self.selected]
                            if self.qm.accept(q["id"]):
                                self._msg=f"Quest accepted: {q['title']}!"
                                available_quests=self.qm.get_available()
                            else:
                                self._msg="Quest log is full! (3 max)"
                            self._msg_t=2.5

                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                    pw2=int(self.W*0.90)
                    px2=self.W//2-pw2//2
                    ph2=int(self.H*0.88)
                    py2=self.H//2-ph2//2
                    for i in range(3):
                        tx=px2+i*(pw2//3)
                        ty=self.H//2-ph2//2+38
                        if pygame.Rect(tx+2,ty,pw2//3-4,32).collidepoint(mouse):
                            self.tab=i; self.selected=0
                    # Quest log button click
                    active_count2=len(self.qm.active)
                    btn_txt2=self.font_small.render(
                        f"[ Q ]  Quest Log  ({active_count2} active)",True,(80,160,80))
                    bx5=px2+pw2-btn_txt2.get_width()-28
                    by5=py2+ph2-btn_txt2.get_height()-16
                    if pygame.Rect(bx5-8,by5-4,btn_txt2.get_width()+16,btn_txt2.get_height()+8).collidepoint(mouse):
                        result2=QuestLogScene(self.screen,self.qm).run()
                        if result2=="exit": return "exit"

            self._draw_bg()
            px3,py3,pw3,ph3=self._draw_panel(ease)
            if ease>0.5:
                title=self.font_title.render("— NOTICE BOARD —",True,(215,180,105))
                self.screen.blit(title,(self.W//2-title.get_width()//2,py3+10))
                self._draw_tabs(px3,py3,pw3,ease)
                if   self.tab==0: self._draw_quests_tab(px3,py3,pw3,ph3)
                elif self.tab==1: self._draw_wanted_tab(px3,py3,pw3,ph3)
                elif self.tab==2: self._draw_notices_tab(px3,py3,pw3,ph3)

                # Quest log button bottom right
                active_count = len(self.qm.active)
                btn_col = (80,160,80) if active_count>0 else (80,62,30)
                btn_txt = self.font_small.render(
                    f"[ Q ]  Quest Log  ({active_count} active)",True,btn_col)
                bx4=px3+pw3-btn_txt.get_width()-20; by4=py3+ph3-btn_txt.get_height()-12
                bg4=pygame.Surface((btn_txt.get_width()+16,btn_txt.get_height()+8),pygame.SRCALPHA)
                bg4.fill((12,8,4,int(180)))
                self.screen.blit(bg4,(bx4-8,by4-4))
                pygame.draw.rect(self.screen,btn_col,(bx4-8,by4-4,btn_txt.get_width()+16,btn_txt.get_height()+8),1)
                self.screen.blit(btn_txt,(bx4,by4))
            self._draw_message()
            pygame.display.flip()


# ---------------------------------------------------------------------------
# Quest Log Scene — active quests overview
# ---------------------------------------------------------------------------

class QuestLogScene:
    def __init__(self, screen, quest_manager: QuestManager):
        self.screen = screen
        self.W,self.H = screen.get_size()
        self.clock  = pygame.time.Clock()
        self.time   = 0.0
        self.qm     = quest_manager
        self.selected = 0
        self.open_anim = 0.0

        self.font_title  = pygame.font.SysFont("courier new", 26, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 16, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 13)
        self.font_tiny   = pygame.font.SysFont("courier new", 11)
        self.font_large  = pygame.font.SysFont("courier new", 22, bold=True)

    def run(self) -> str:
        while True:
            dt=self.clock.tick(60)/1000.0
            self.time+=dt
            self.open_anim=min(self.open_anim+dt,0.35)
            ease=1-(1-min(1.0,self.open_anim/0.35))**3

            for event in pygame.event.get():
                if event.type==pygame.QUIT: return "exit"
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE: return "back"
                    if event.key==pygame.K_UP:
                        self.selected=max(0,self.selected-1)
                    if event.key==pygame.K_DOWN:
                        self.selected=min(len(self.qm.active)-1,self.selected+1) if self.qm.active else 0
                    if event.key==pygame.K_DELETE and self.qm.active:
                        if 0<=self.selected<len(self.qm.active):
                            self.qm.abandon(self.qm.active[self.selected]["id"])
                            self.selected=max(0,self.selected-1)

            # Draw
            for y in range(self.H):
                t=y/self.H
                pygame.draw.line(self.screen,(int(8+14*t),int(5+9*t),int(3+6*t)),(0,y),(self.W,y))

            pw=int(self.W*0.82); ph=int(self.H*0.86)
            px=self.W//2-pw//2; py=self.H//2-ph//2
            w2=int(pw*ease); h2=int(ph*ease)
            x2=self.W//2-w2//2; y2=self.H//2-h2//2
            if w2>4:
                bg=pygame.Surface((w2,h2),pygame.SRCALPHA)
                bg.fill((14,10,6,248)); self.screen.blit(bg,(x2,y2))
                pygame.draw.rect(self.screen,(130,100,48),(x2,y2,w2,h2),2)
                sz=13
                for bx,by,dx,dy in [(x2,y2,1,1),(x2+w2,y2,-1,1),(x2,y2+h2,1,-1),(x2+w2,y2+h2,-1,-1)]:
                    pygame.draw.line(self.screen,(180,145,65),(bx,by),(bx+dx*sz,by),2)
                    pygame.draw.line(self.screen,(180,145,65),(bx,by),(bx,by+dy*sz),2)

            if ease>0.6:
                title=self.font_title.render("— QUEST LOG —",True,(215,180,105))
                self.screen.blit(title,(self.W//2-title.get_width()//2,py+12))
                pygame.draw.line(self.screen,(130,100,48),(px+20,py+44),(px+pw-20,py+44),1)

                # Completed count
                cc=self.font_tiny.render(
                    f"Completed: {len(self.qm.completed)}    Active: {len(self.qm.active)}/{self.qm.MAX_ACTIVE}",
                    True,(100,78,38))
                self.screen.blit(cc,(px+pw-cc.get_width()-16,py+14))

                if not self.qm.active:
                    ns=self.font_medium.render("No active quests — visit the Notice Board!",
                                                True,(80,62,30))
                    self.screen.blit(ns,(self.W//2-ns.get_width()//2,py+ph//2))
                else:
                    row_h=110; start_y=py+55
                    for i,q in enumerate(self.qm.active):
                        ry=start_y+i*row_h
                        is_sel=(i==self.selected)
                        diff_col=DIFFICULTY_COL.get(q["difficulty"],(150,150,150))
                        row_w=pw-32

                        bg2=pygame.Surface((row_w,row_h-8),pygame.SRCALPHA)
                        bg2.fill((int(20+20*(1 if is_sel else 0)),
                                  int(14+14*(1 if is_sel else 0)),
                                  int(8+8*(1 if is_sel else 0)),220))
                        self.screen.blit(bg2,(px+16,ry))
                        bc=(180,145,65) if is_sel else (55,42,22)
                        pygame.draw.rect(self.screen,bc,(px+16,ry,row_w,row_h-8),2 if is_sel else 1)

                        if is_sel:
                            arr=self.font_small.render("▶",True,(180,148,60))
                            self.screen.blit(arr,(px+4,ry+row_h//2-arr.get_height()//2))

                        # Title + difficulty
                        ts2=self.font_medium.render(q["title"],True,(225,195,130))
                        self.screen.blit(ts2,(px+24,ry+8))
                        ds2=self.font_tiny.render(DIFFICULTY_STARS[q["difficulty"]],True,diff_col)
                        self.screen.blit(ds2,(px+24+ts2.get_width()+10,ry+10))

                        # Description
                        desc_s2=self.font_small.render(q["desc"],True,(155,125,65))
                        self.screen.blit(desc_s2,(px+24,ry+28))

                        # Progress bar
                        prog=q["progress"]; req=q["required"]
                        prog_frac=min(1.0,prog/req) if req>0 else 0
                        bar_w=int(row_w*0.55); bar_h=12
                        bx3=px+24; by3=ry+50
                        pygame.draw.rect(self.screen,(30,22,14),(bx3,by3,bar_w,bar_h))
                        pygame.draw.rect(self.screen,(65,48,25),(bx3,by3,bar_w,bar_h),1)
                        if prog_frac>0:
                            fill_col=(50,180,60) if prog_frac<1.0 else (180,160,50)
                            pygame.draw.rect(self.screen,fill_col,(bx3,by3,int(bar_w*prog_frac),bar_h))
                        prog_s=self.font_tiny.render(f"{prog}/{req}",True,(160,140,80))
                        self.screen.blit(prog_s,(bx3+bar_w+8,by3))

                        # Reward summary
                        rew=f"Reward: {q['reward_gold']}g  +{q['reward_exp']} EXP"
                        if q.get("reward_item"): rew+=f"  +{q['reward_item'].replace('Item','')}"
                        rs2=self.font_tiny.render(rew,True,(160,140,65))
                        self.screen.blit(rs2,(px+24,ry+68))

                        # Complete indicator
                        if prog>=req:
                            done=self.font_medium.render("✓ COMPLETE — return to notice board",
                                                          True,(80,200,80))
                            self.screen.blit(done,(px+row_w-done.get_width()-8,ry+row_h-30))

                hint=self.font_tiny.render("↑ ↓  select    DEL  abandon quest    ESC  back",
                                            True,(70,54,28))
                self.screen.blit(hint,(self.W//2-hint.get_width()//2,py+ph-hint.get_height()-10))

            pygame.display.flip()
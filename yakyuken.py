import pyxel
import random
from enum import Enum
from math import sqrt

# ウインドウ設定
WINDOW_HEIGHT = 256
WINDOW_WIDTH = 256
TITLE = 'LIMITED YAKYU KEN'
FPS = 60

# カードの色
GU = pyxel.COLOR_RED            # グー
CH = pyxel.COLOR_GREEN          # チョキ
PA = pyxel.COLOR_LIGHT_BLUE     # パー

# カードの大きさ
CARD_W = 13.5
CARD_H = 24

# 手札の枚数
HAND_MAX = 5
# 手札表示幅
HAND_W = (CARD_W + 5) * HAND_MAX + 5

# テキスト表示
FONT_JP = pyxel.Font('assets/umplus_j10r.bdf')
MSG_BOX_TOP = WINDOW_HEIGHT - 50

# プレイヤー操作
CTRL_PLAYER = 1
# コンピュータ操作
CTRL_COM = 2

# カード捲り用変数
CARD_OPEN_OFFSET = sqrt(CARD_W)
CARD_OP_ADD = CARD_OPEN_OFFSET / (FPS / 2)

# ライフ最大値
LIFE_MAX = 5
ONE_LIFE_W = 12

# ダメージ表現実施時間
DAMAGE_WAIT = 60


class GameState(Enum):
    '''
    ゲーム状態遷移定数
    '''
    TITLE = 0       # タイトル画面
    INIT = 1        # 最初に１度だけ行う処理
    SELECT = 2      # カード選択
    OPEN = 3        # COMのカード表示
    RESULT = 4      # じゃんけん結果
    GAME_SET = 5    # 決着
    END = 6         # リセット待ち状態


class CardState(Enum):
    MOVING = 0      # 移動中
    WAIT = 1        # 待機状態
    LOCK = 2        # カードに触っても反応させない
    ROTATION = 3    # めくりの回転中


class CharaState(Enum):
    WAIT = 0        # 待機中
    DAMAGE = 1      # ダメージ演出中


class LifeState(Enum):
    WAIT = 0        # 待機中
    DECRASE = 1     # Life減少中


class MsgState(Enum):
    WAIT = 0        # 待機中
    DISPLAYING = 1  # メッセージ表示中


class ObjectBase:
    '''
    いろんなオブジェクトのペース
    '''
    def __init__(self, x: float, y: float,
                 w: float, h: float):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.is_mouse_over = False

    def IsOverMouse(self) -> bool:
        '''
        オブジェクト上にマウスがあるか？
        '''
        return self.x < pyxel.mouse_x < self.x + self.w \
            and self.y < pyxel.mouse_y < self.y + self.h

    def LineRect(self, inner_color: int, outer_color: int):
        '''
        枠線のある四角を描画
        '''
        pyxel.rectb(self.x, self.y, self.w, self.h, outer_color)
        pyxel.rect(self.x + 1, self.y + 1, self.w - 2, self.h - 2, inner_color)


class Card(ObjectBase):
    '''
    カードクラス
    '''
    def __init__(self, x: float, y: float, pos: int,
                 type: int, is_show: bool, is_big: bool = False):
        # 表示サイズによる初期化
        self.is_big = is_big
        # x_pos 目的地
        if is_big:
            self.x_pos = x
            dx = x - CARD_W * 2
            if is_show is False:
                dx = x + CARD_W * 2
            super().__init__(dx, y, CARD_W * 2, CARD_H * 2)
        else:
            self.x_pos = x + (CARD_W + 5) * pos + 5
            super().__init__(x - CARD_W, y + 5, CARD_W, CARD_H)

        self.type = type            # グー/チョキ/パー
        self.is_show = is_show      # 表面にするか否か
        self.state = CardState.MOVING
        self.is_selected = False    # 手札から選択中
        self.x_offset = CARD_OPEN_OFFSET * -1

    def update(self):
        '''
        データ更新
        '''
        if CardState.MOVING == self.state:
            # 所定の位置へ移動
            dx = abs(self.x_pos - self.x) / 10.0
            if self.is_show is False and self.is_big:
                self.x -= dx
            else:
                self.x += dx
            if self.x - 0.1 <= self.x_pos <= self.x + 0.1:
                self.state = CardState.WAIT
                self.x = self.x_pos

        elif CardState.WAIT == self.state:
            if self.is_big or self.is_show is False:
                return

            # マウス操作 ハイライト表示
            self.is_mouse_over = self.IsOverMouse()
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) \
                    and pyxel.mouse_y < MSG_BOX_TOP:
                self.is_selected = self.is_mouse_over

        elif CardState.ROTATION == self.state:
            # COMのカード捲り動作中
            if self.x_offset < CARD_OPEN_OFFSET:
                self.x_offset += CARD_OP_ADD
            else:
                # めくり終わったら待機状態へ
                self.x_offset = CARD_OPEN_OFFSET
                self.state = CardState.WAIT

            if 0 < self.x_offset:
                self.is_show = True

    def draw(self):
        '''
        描画
        '''
        if self.is_selected:
            return

        # 非表示の色
        color = pyxel.COLOR_PURPLE
        if self.is_show:
            # 表示の場合、各々の色を設定
            color = self.type

        # COM用めくりのオフセット計算
        offset = 0
        if CardState.ROTATION == self.state:
            offset = (-1 * (self.x_offset * self.x_offset)) + CARD_W
        # カード本体
        pyxel.rect(self.x + offset, self.y, self.w - (offset * 2),
                   self.h, pyxel.COLOR_GRAY)
        pyxel.rect(self.x + 1 + offset, self.y + 1,
                   self.w - 2 - (offset * 2), self.h - 2, color)
        # カードの柄
        txt = '?'
        if self.is_show:
            if self.type == GU:
                txt = 'G'
            elif self.type == CH:
                txt = 'C'
            else:
                txt = 'P'
        pyxel.text(self.x + self.w / 2 - 3, self.y + self.h / 2 - 4,
                   txt, pyxel.COLOR_WHITE, FONT_JP)
        # ハイライト表示
        if self.is_mouse_over and self.is_show:
            pyxel.rectb(self.x - 1, self.y - 1,
                        self.w + 2, self.h + 2,
                        pyxel.COLOR_WHITE)

    def ResetPos(self, x, pos):
        '''
        カード位置変更
        '''
        self.x = x + (CARD_W + 5) * pos + 5

    def SetLock(self, islock: bool):
        '''
        一時的にカードを触れないようにする
        '''
        if islock:
            self.state = CardState.LOCK
        else:
            self.state = CardState.WAIT


class Deck(ObjectBase):
    '''
    カードをまとめた山札・手札クラス
    '''
    def __init__(self, x: float, y: float, is_show: bool):
        h = CARD_H + 10
        super().__init__(x, y, HAND_W, h)
        # カードの表示・非表示
        self.is_show = is_show

        g = [GU] * 10
        c = [CH] * 10
        p = [PA] * 10
        # シャッフルして山札へセット
        self.cards = self.Shuffle(g, c, p)

        # 山札から手札をドローする
        self.hands = []
        cnt = 0
        for _ in range(HAND_MAX):
            card = self.cards.pop()
            self.hands.append(Card(self.x, self.y, cnt,
                                   card, self.is_show))
            cnt += 1

        # 場に出しているカード
        self.selected_card = None
        self.selected_idx = -1

    def update(self, px: float, side: int):
        '''
        データ更新
        '''
        if self.is_show is False:
            self.RandomPick()

        select_cnt = 0
        idx = -1
        hnd: Card
        for hnd in self.hands:
            hnd.update()
            idx += 1
            # 選択中のカードを場に出す
            if hnd.is_selected:
                # 別のインデックスを選択したときにインスタンスを入れ替える
                if self.selected_idx != idx:
                    dx = 0
                    if side == CTRL_PLAYER:
                        dx = px + pyxel.width / 2 - CARD_W * 2 - 5
                    else:
                        dx = px + 5
                    self.selected_card = self.CreateBigCard(dx, hnd.type)
                    self.selected_idx = idx
                select_cnt += 1

        if select_cnt <= 0:
            # 何も選んでないときは表示しない
            self.selected_card = None
            self.selected_idx = -1

        if self.selected_card is not None:
            # 選んでいる場合更新する。
            self.selected_card.update()

    def draw(self):
        '''
        描画
        '''
        self.LineRect(pyxel.COLOR_BLACK, pyxel.COLOR_GRAY)
        hnd: Card
        for hnd in self.hands:
            hnd.draw()
        if self.selected_card is not None:
            self.selected_card.draw()

    def CreateBigCard(self, x: float, type: int) -> Card:
        '''
        対決用の大きい表示のカードを作成
        '''
        return Card(x, pyxel.height / 2 - CARD_H, 0,
                    type, self.is_show, True)

    def Shuffle(self, g: list[int], c: list[int],
                p: list[int]) -> list[int]:
        '''
        シャッフル
        '''
        random.seed()
        ary = g + c + p
        rand_ary = []
        for item in ary:
            rand_ary.append({'key': item,
                             'value': random.randrange(255)})
        sort_ary = sorted(rand_ary, key=lambda x: x['value'])
        return [d.get('key') for d in sort_ary]

    def RandomPick(self):
        '''
        COM用、ランダムに手札を選ぶ
        '''
        if self.selected_card is not None:
            return
        if self.IsAllInit() is False:
            return

        hand_cnt = len(self.hands)
        idx = pyxel.rndi(0, hand_cnt - 1)
        for i in range(hand_cnt):
            self.hands[i].is_selected = i == idx

    def IsAllInit(self) -> bool:
        '''
        手札全部所定の位置についたか？
        '''
        cnt = 0
        hnd: Card
        for hnd in self.hands:
            if hnd.state == CardState.WAIT:
                cnt += 1
        return cnt == len(self.hands)

    def CardOpen(self):
        '''
        COM用, カードを開く
        '''
        if self.is_show is False and self.selected_card is not None:
            self.selected_card.state = CardState.ROTATION
            self.selected_card.x_offset = CARD_OPEN_OFFSET * -1

    def SelectClear(self):
        '''
        選択カードを手札に戻す
        '''
        hnd: Card
        for hnd in self.hands:
            hnd.is_selected = False

    def HandDrow(self):
        '''
        山札から手札を補充します。
        '''
        # 左詰めで手札を整理する
        tmp = []
        pos = 0
        while self.hands:
            h: Card = self.hands.pop()
            if h.is_selected is False:
                h.ResetPos(self.x, pos)
                tmp.append(h)
                pos += 1
        while tmp:
            self.hands.append(tmp.pop())

        # 右端に山札からのカードをセットする
        if 0 < len(self.cards):
            card = self.cards.pop()
            self.hands.append(Card(self.x, self.y, len(self.hands),
                                   card, self.is_show))

    def HandLock(self):
        '''
        カードのクリック動作無効化
        '''
        hnd: Card
        for hnd in self.hands:
            hnd.SetLock(True)

    def HandUnlock(self):
        '''
        カードのクリック動作有効化
        '''
        hnd: Card
        for hnd in self.hands:
            hnd.SetLock(False)


class LifeBox(ObjectBase):
    '''
    ライフゲージクラス
    '''
    def __init__(self, x, y):
        w = ONE_LIFE_W * LIFE_MAX + 2
        super().__init__(x, y, w, 12)
        self.life = LIFE_MAX
        self.offset = 0
        self.next = 0
        self.state = LifeState.WAIT

    def update(self):
        '''
        データ更新
        '''
        if self.state == LifeState.DECRASE:
            if self.offset < self.next:
                self.offset += 0.1
            else:
                self.state = LifeState.WAIT

    def draw(self):
        '''
        描画
        '''
        # 外枠
        pyxel.rectb(self.x + 30, self.y, self.w, self.h,
                    pyxel.COLOR_GRAY)
        # 背景色
        pyxel.rect(self.x + 31, self.y + 1,
                   self.w - 2, self.h - 2, pyxel.COLOR_RED)
        # ライフゲージ
        pyxel.rect(self.x + 31, self.y + 1,
                   self.w - 2 - self.offset, self.h - 2,
                   pyxel.COLOR_GREEN)
        # ラベル
        pyxel.text(self.x, self.y + 2, 'Life',
                   pyxel.COLOR_WHITE, FONT_JP)

    def Damege(self, dmg: int):
        '''
        ライフゲージをダメージ分減らす
        '''
        self.life -= dmg
        self.next = (LIFE_MAX - self.life) * ONE_LIFE_W
        self.state = LifeState.DECRASE


class Character(ObjectBase):
    '''
    キャラクタクラス
    '''
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 60, 120)
        self.e_val_a = pyxel.rndi(-60, 60)
        self.y_base = y
        self.x_base = x
        self.state = CharaState.WAIT

        self.e_val_b = 0        # 横揺れ変数
        self.cnt = DAMAGE_WAIT  # 横揺れ時間

    def update(self):
        '''
        データ更新
        '''
        # キャラクタに動きを与える
        self.e_val_a += 1
        if FPS < self.e_val_a:
            self.e_val_a = FPS * -1
        self.y = self.Wave(self.y_base, self.e_val_a, 1200)

        # ダメージ横揺れ
        if self.state == CharaState.DAMAGE:
            self.e_val_b += 10
            if FPS < self.e_val_b:
                self.e_val_b = FPS * -1
            self.x = self.Wave(self.x_base, self.e_val_b, 3600)
            self.cnt -= 1
            if self.cnt < 0:
                self.state = CharaState.WAIT

    def draw(self, lifebox: LifeBox):
        '''
        描画
        '''
        idx = LIFE_MAX - lifebox.life
        # debug
        pyxel.rect(self.x, self.y,
                   self.w, self.h, pyxel.COLOR_WHITE + idx)

    def Wave(self, offset: float, a: float, b: float) -> float:
        '''
        ゆらゆら揺れる位置情報の計算
        '''
        return offset + (a * a) / b

    def SetDamage(self):
        '''
        ダメージ演出セット
        '''
        self.cnt = DAMAGE_WAIT
        self.state = CharaState.DAMAGE


class Player(ObjectBase):
    '''
    対戦するキャラクタのクラス
    '''
    def __init__(self, type: int):
        self.type = type
        if self.type == CTRL_PLAYER:
            super().__init__(0, 0,
                             pyxel.width / 2, pyxel.height)
        else:
            super().__init__(pyxel.width / 2, 0,
                             pyxel.width / 2, pyxel.height)
        dec_x = self.x + self.w / 2 - HAND_W / 2
        # 手札位置セット
        self.deck = Deck(dec_x, self.y + 5, self.type == CTRL_PLAYER)
        # ライフゲージセット
        self.life = LifeBox(self.deck.x + 2,
                            self.deck.y + self.deck.h + 5)
        # キャラクターセット
        self.chara = Character(self.x + self.w / 2 - 30,
                               self.y + self.deck.y + self.deck.h + 20)

    def update(self):
        '''
        データ更新
        '''
        self.deck.update(self.x, self.type)
        self.chara.update()
        self.life.update()

    def draw(self):
        '''
        描画
        '''
        self.chara.draw(self.life)
        self.deck.draw()
        self.life.draw()


class Button(ObjectBase):
    '''
    クリックで動作するボタンクラス
    '''
    def __init__(self, x: float, y: float, txt: str):
        w = FONT_JP.text_width(txt)
        super().__init__(x, y, w + 8, 19)
        self.text = txt

    def IsClick(self) -> bool:
        '''
        クリック判定
        '''
        return pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) \
            and self.IsOverMouse()

    def update(self):
        '''
        データ更新
        '''
        self.is_mouse_over = self.IsOverMouse()

    def draw(self):
        '''
        描画
        '''
        if self.is_mouse_over:
            self.LineRect(pyxel.COLOR_YELLOW, pyxel.COLOR_GRAY)
        else:
            self.LineRect(pyxel.COLOR_WHITE, pyxel.COLOR_GRAY)
        pyxel.text(self.x + 4, self.y + 4, self.text,
                   pyxel.COLOR_BLACK, FONT_JP)


class ChooseBox(ObjectBase):
    '''
    選択肢クラス
    '''
    def __init__(self, y: float):
        w = FONT_JP.text_width('YesNo') + 10
        x = pyxel.width - w - 20
        self.yes_btn = Button(x + 2, y + 2, 'Yes')
        self.no_btn = Button(self.yes_btn.x + self.yes_btn.w + 2,
                             y + 2, 'No')
        super().__init__(x, y, self.no_btn.w + self.no_btn.w + 6, 18)

    def update(self):
        '''
        データ更新
        '''
        self.yes_btn.update()
        self.no_btn.update()

    def draw(self):
        '''
        描画
        '''
        self.yes_btn.draw()
        self.no_btn.draw()

    def IsYes(self) -> bool:
        '''
        Yesボタンをクリックした
        '''
        return self.yes_btn.IsClick()

    def IsNo(self) -> bool:
        '''
        Noボタンをクリックした
        '''
        return self.no_btn.IsClick()


class MessageBox(ObjectBase):
    '''
    メッセージ表示エリアクラス
    '''
    def __init__(self):
        super().__init__(5, MSG_BOX_TOP, pyxel.width - 10, 40)
        self.msg = []
        self.state = MsgState.WAIT
        self.disp = ''

    def update(self):
        '''
        データ更新
        '''
        if MsgState.WAIT == self.state:
            pass
        elif MsgState.DISPLAYING == self.state:
            if 0 < len(self.msg):
                if pyxel.frame_count % 4 == 0:
                    self.disp += self.msg.pop(0)
            else:
                self.state = MsgState.WAIT

    def draw(self):
        '''
        描画
        '''
        self.LineRect(pyxel.COLOR_WHITE, pyxel.COLOR_GRAY)
        pyxel.text(self.x + 2, self.y + 2, self.disp,
                   pyxel.COLOR_BLACK, FONT_JP)

    def SetMessage(self, msg: str):
        '''
        メッセージをセットする
        '''
        self.msg.clear()
        for s in msg:
            self.msg.append(s)
        self.state = MsgState.DISPLAYING
        self.disp = ''

    def Clear(self):
        '''
        メッセージを消去
        '''
        self.msg.clear()
        self.state = MsgState.WAIT
        self.disp = ''


class App:
    def __init__(self):
        pyxel.init(WINDOW_WIDTH, WINDOW_HEIGHT,
                   title=TITLE, fps=FPS, display_scale=2)
        pyxel.mouse(True)
        self.ReadResources()
        self.DefineVariables()
        pyxel.run(self.update, self.draw)

    def ReadResources(self):
        '''
        リソースファイルの読み込み
        '''
        pyxel.images[0].load(0, 0, 'assets/Pallet.png', incl_colors=True)

    def DefineVariables(self):
        '''
        内部変数初期化
        '''
        self.player = Player(CTRL_PLAYER)
        self.com = Player(CTRL_COM)
        self.msg_box = MessageBox()
        self.game_sate = GameState.TITLE
        self.choose = None
        self.wait = 0

    def update(self):
        '''
        データ更新
        '''
        if GameState.TITLE != self.game_sate:
            self.player.update()
            self.com.update()
            self.msg_box.update()

        if GameState.TITLE == self.game_sate:
            # タイトル画面
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.game_sate = GameState.INIT

        elif GameState.INIT == self.game_sate:
            if self.player.deck.IsAllInit():
                if self.msg_box.state == MsgState.WAIT:
                    # ゲーム開始前の初期化
                    self.msg_box.SetMessage('Choose your card')
                    self.game_sate = GameState.SELECT

        elif GameState.SELECT == self.game_sate:
            # 初期動作、カードを選択するまでの処理
            if self.choose is None:
                # 選択肢表示するか？
                if self.player.deck.selected_card is not None \
                        and self.com.deck.selected_card is not None \
                        and self.msg_box.state == MsgState.WAIT:
                    self.choose = ChooseBox(self.msg_box.y + 2)
                    self.msg_box.SetMessage('Ready?')
            else:
                if self.player.deck.selected_card is None \
                        or self.com.deck.selected_card is None:
                    # 選択肢非表示
                    self.choose = None
                    self.msg_box.Clear()
                else:
                    # 選択肢での選択処理
                    self.choose.update()
                    if self.choose.IsYes():
                        self.msg_box.SetMessage('Battle Start!')
                        self.com.deck.CardOpen()
                        self.wait = 60
                        self.choose = None
                        self.player.deck.HandLock()
                        self.game_sate = GameState.OPEN
                    elif self.choose.IsNo():
                        self.player.deck.SelectClear()

        elif GameState.OPEN == self.game_sate:
            # カードをめくった後の動作
            if self.player.deck.selected_card.state == CardState.WAIT \
                    and self.com.deck.selected_card.state == CardState.WAIT \
                    and self.msg_box.state == MsgState.WAIT:
                self.wait -= 1
            if self.wait < 0:
                # じゃんけん勝負を行い結果によりダメージ判定
                result = self.Battle()
                if 0 < result:
                    self.com.life.Damege(1)
                    self.msg_box.SetMessage('COM Damege!')
                    self.com.chara.SetDamage()
                if result < 0:
                    self.player.life.Damege(1)
                    self.msg_box.SetMessage('Player Damege!')
                    self.player.chara.SetDamage()
                if result == 0:
                    self.msg_box.SetMessage('Drow!')
                self.wait = 60
                if self.IsEnd():
                    self.game_sate = GameState.GAME_SET
                else:
                    self.game_sate = GameState.RESULT

        elif GameState.RESULT == self.game_sate:
            # カードを補充する
            if self.player.life.state == LifeState.WAIT \
                    and self.com.life.state == LifeState.WAIT \
                    and self.msg_box.state == MsgState.WAIT:
                self.wait -= 1
            if self.wait < 0:
                self.player.deck.HandUnlock()
                self.msg_box.SetMessage('Hand card drow')
                self.player.deck.HandDrow()
                self.com.deck.HandDrow()
                self.game_sate = GameState.INIT

        elif GameState.GAME_SET == self.game_sate:
            # 勝ち負けの表示
            if self.player.life.state == LifeState.WAIT \
                    and self.com.life.state == LifeState.WAIT \
                    and self.msg_box.state == MsgState.WAIT \
                    and 0 < self.wait:
                self.wait -= 1
            if self.wait <= 0:
                if self.player.life.life <= 0:
                    self.msg_box.SetMessage('COM Win!')
                elif self.com.life.life <= 0:
                    self.msg_box.SetMessage('Player Win!')
                else:
                    self.msg_box.SetMessage('No contest ...')
                self.game_sate = GameState.END

        elif GameState.END == self.game_sate:
            # リセット待ち
            if pyxel.btnp(pyxel.KEY_R):
                self.player = Player(CTRL_PLAYER)
                self.com = Player(CTRL_COM)
                self.msg_box = MessageBox()
                self.game_sate = GameState.INIT
                self.choose = None
                self.wait = 0

    def draw(self):
        '''
        描画
        '''
        pyxel.cls(pyxel.COLOR_NAVY)

        if GameState.TITLE == self.game_sate:
            top = pyxel.height / 2 - 5
            self.DrawTextCenter(top, TITLE,
                                pyxel.COLOR_WHITE, pyxel.COLOR_RED)
            self.DrawTextCenter(top + 15, 'Click to start',
                                pyxel.COLOR_WHITE, pyxel.COLOR_NAVY)
        else:
            self.player.draw()
            self.com.draw()
            self.msg_box.draw()
            if self.choose is not None:
                self.choose.draw()

        # debug
        if self.com.deck.selected_card is not None:
            pyxel.rect(pyxel.width - 4, pyxel.height - 4,
                       4, 4, self.com.deck.selected_card.type)

    def Battle(self) -> int:
        '''
        じゃんけんの勝負判定
        '''
        pt = self.player.deck.selected_card.type
        ct = self.com.deck.selected_card.type

        # あいこ
        if pt == ct:
            return 0

        # プレイヤーの勝ちパターン
        if pt == GU and ct == CH:
            return 1
        if pt == CH and ct == PA:
            return 1
        if pt == PA and ct == GU:
            return 1

        # それ以外は負け
        return -1

    def DrawTextCenter(self, y: float, s: str,
                       col: int, bcol: int = None):
        '''
        縁取りテキスト描画
        '''
        # 中央寄せ
        x = (pyxel.width / 2) - (FONT_JP.text_width(s) / 2)
        if bcol is None:
            bcol = pyxel.COLOR_BLACK
        # アウトライン描画
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx != 0 or dy != 0:
                    pyxel.text(x + dx, y + dy, s, bcol, FONT_JP)
        pyxel.text(x, y, s, col, FONT_JP)

    def IsEnd(self) -> bool:
        '''
        決着がついたか？
        '''
        # どちらかがやられた
        if self.player.life.life <= 0:
            return True
        if self.com.life.life <= 0:
            return True

        # カード残り 0
        if len(self.player.deck.cards) <= 0:
            return True
        if len(self.com.deck.cards) <= 0:
            return True

        return False


# 開始
App()

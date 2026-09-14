export type Locale = "zh" | "en";

export interface TarotCard {
  id: string;
  name: string;
  nameZh: string;
  number: number;
  suit: "major" | "wands" | "cups" | "swords" | "pentacles";
  imageUrl: string;
}

const commonsFile = (filename: string) =>
  `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(filename)}`;

const major = [
  ["The Fool", "愚人", "Fool"],
  ["The Magician", "魔术师", "Magician"],
  ["The High Priestess", "女祭司", "High_Priestess"],
  ["The Empress", "皇后", "Empress"],
  ["The Emperor", "皇帝", "Emperor"],
  ["The Hierophant", "教皇", "Hierophant"],
  ["The Lovers", "恋人", "Lovers"],
  ["The Chariot", "战车", "Chariot"],
  ["Strength", "力量", "Strength"],
  ["The Hermit", "隐士", "Hermit"],
  ["Wheel of Fortune", "命运之轮", "Wheel_of_Fortune"],
  ["Justice", "正义", "Justice"],
  ["The Hanged Man", "倒吊人", "Hanged_Man"],
  ["Death", "死神", "Death"],
  ["Temperance", "节制", "Temperance"],
  ["The Devil", "恶魔", "Devil"],
  ["The Tower", "高塔", "Tower"],
  ["The Star", "星星", "Star"],
  ["The Moon", "月亮", "Moon"],
  ["The Sun", "太阳", "Sun"],
  ["Judgement", "审判", "Judgement"],
  ["The World", "世界", "World"],
] as const;

const majorCards: TarotCard[] = major.map(([name, nameZh, file], number) => ({
  id: `major_${String(number).padStart(2, "0")}`,
  name,
  nameZh,
  number,
  suit: "major",
  imageUrl: commonsFile(`RWS_Tarot_${String(number).padStart(2, "0")}_${file}.jpg`),
}));

const ranks = [
  ["Ace", "王牌", "ace"],
  ["Two", "二", "02"],
  ["Three", "三", "03"],
  ["Four", "四", "04"],
  ["Five", "五", "05"],
  ["Six", "六", "06"],
  ["Seven", "七", "07"],
  ["Eight", "八", "08"],
  ["Nine", "九", "09"],
  ["Ten", "十", "10"],
  ["Page", "侍从", "page"],
  ["Knight", "骑士", "knight"],
  ["Queen", "皇后", "queen"],
  ["King", "国王", "king"],
] as const;

const suits = [
  ["wands", "Wands", "权杖", "Wands"],
  ["cups", "Cups", "圣杯", "Cups"],
  ["swords", "Swords", "宝剑", "Swords"],
  ["pentacles", "Pentacles", "星币", "Pents"],
] as const;

const minorCards: TarotCard[] = suits.flatMap(
  ([suit, englishSuit, chineseSuit, filePrefix]) =>
    ranks.map(([rank, rankZh, idRank], index) => ({
      id: `${suit}_${idRank}`,
      name: `${rank} of ${englishSuit}`,
      nameZh: `${chineseSuit}${rankZh}`,
      number: index + 1,
      suit,
      imageUrl: commonsFile(`${filePrefix}${String(index + 1).padStart(2, "0")}.jpg`),
    })),
);

export const tarotDeck: TarotCard[] = [...majorCards, ...minorCards];

export const localizedCardName = (card: TarotCard, locale: Locale) =>
  locale === "zh" ? card.nameZh : card.name;

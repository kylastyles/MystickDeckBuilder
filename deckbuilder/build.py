import logging
import os
import pandas as pd
import random
import sys
from math import floor
from statistics import mean

from models.card import Card
from models.deck import Deck

logger = logging.getLogger()
logger.setLevel("DEBUG")
logger.addHandler(logging.StreamHandler(sys.stdout))

NUM_DECKS = 5
CARD_CATALOG_FILE="./deckbuilder/data/MystickCardLibrary.csv"

class NotEnoughCardsError(Exception):
    """
    Throw this exception whenever the Library lacks the cards
    to satisfy a deck-building condition.
    """
    pass


class DeckBuilder:
    """
    At the core of the DeckBuilder is the Library; a Pandas DataFrame that is a collection of all available Cards.
    The DeckBuilder uses the Game Rules to pull suitable Cards from the Library to build a Deck.
    """
    # == Game Rules ==
    MAX_SUITS = 2
    MAX_MJR_ARCANA = 11
    MAX_SUIT_CARDS = 14
    TOTAL_DECK = 39
    # some versions of game play allow for doubles, ie cards of same suit and rank in one deck.
    DOUBLES = False

    def __init__(self):
        """
        Initialize the DeckBuilder's Library.
        """
        self.library = pd.read_csv(CARD_CATALOG_FILE)
        self.library["new_index"] = self.library.loc[:, "ID"]
        self.library = self.library.set_index("new_index")

        self.all_suits = list(pd.unique(self.library["Suit"])[1:])
        # self.minor_ranks = list(pd.unique(self.library["Rank"].where(self.library["Suit"] != "Major Arcana"))[1:])
        # self.major_ranks = list(pd.unique(self.library["Rank"].where(self.library["Suit"] == "Major Arcana"))[:-1])

        # These Major Arcana cards help the associated suit. We prevent adding them to decks of other suits.
        self.affinity_majors = {
            "Wands": "MJR_1",
            "Cups": "MJR_6",
            "Swords": "MJR_2",
            "Pentacles": "MJR_4"
        }

    def __card_pick(self, suit, rank):
        """
        Returns one available Card that matches the given suit and rank.
        """
        card_options = self.library[
            (self.library["Suit"] == suit) &
            (self.library["Rank"] == rank) &
            (self.library["Copies"] > 0)
        ]
        if len(card_options) == 0:
            raise NotEnoughCardsError(f"ERROR: No more cards of {suit} {rank} remain in Library.")

        card = Card(card_options.sample(n=1).to_dict(orient="records")[0])
        # remove card from library
        self.library.loc[card.ID, "Copies"] = card.Copies - 1

        return card

    def __return_card_to_library(self, c):
        """
        Add a specified Card's copy back to the Library.
        """
        self.library[self.library["ID"] == c.ID]["Copies"].apply(lambda x: x + 1)
        return

    def __return_deck_to_library(self, deck):
        """
        Add all Cards in a Deck back to the Library.
        """
        for c in deck.Major_cards:
            self.__return_card_to_library(c)
        for c in deck.Minor_cards:
            self.__return_card_to_library(c)
        return

    def __available_suits(self):
        """
        Returns a list of suits that contain enough Cards to form a Deck.
        """
        available = []

        for s in self.all_suits:
            card_sum = self.library[self.library["Suit"] == s]["Copies"].sum()

            if card_sum >= DeckBuilder.MAX_SUIT_CARDS:
                available.append(s)

        if len(available) < DeckBuilder.MAX_SUITS:
            raise NotEnoughCardsError("ERROR: Not enough complete suits to create a deck.")

        return available

    def __available_ranks_in_suit(self, suit, exclude=None):
        """
        Returns a list of ranks of all Cards in the specified suit with copies > 0.
        Also takes an optional list of Card ID's to exclude from selection.
        """
        if exclude:
            available_cards = self.library[
                (self.library["Suit"] == suit) &
                (self.library["Copies"] > 0) &
                (~self.library["ID"].isin(exclude))
                ]["Rank"].to_list()
        else:
            available_cards = self.library[
                (self.library["Suit"] == suit) &
                (self.library["Copies"] > 0)
                ]["Rank"].to_list()

        if not available_cards:
            raise NotEnoughCardsError(f"ERROR: {suit} suit is empty.")

        return available_cards

    def balance_decks(self, decks):
        print(f"Balancing {len(decks)} decks...")
        avg = mean([d.Power for d in decks])
        reshuffle = True

        while reshuffle:
            reshuffled_decks = 0
            for d in decks:
                diff = floor(d.Power - avg)
                # deck not too far from mean, no reshuffling needed
                if diff < 2:
                    print("Not reshuffling one deck")
                    continue

                print("Reshuffling a deck")
                self.__return_deck_to_library(d)
                reshuffled_decks += 1

            for i in range(reshuffled_decks):
                try:
                    decks.append(self.build_deck(f"new_{i}"))
                except NotEnoughCardsError:
                    print("=== Stopping reshuffling due to out of cards ===")
                    return decks

            uneven = any(floor(d.Power - avg) > 2 for d in decks)
            if not uneven:
                print("=== Stopping reshuffling due to even decks ===")
                reshuffle = False

            return decks


    def build_deck(self, name=None):
        """
        Build a Deck from the library according to the Game Rules.
        """
        # pick suits for this deck
        avail_suits = self.__available_suits()
        if len(avail_suits) < DeckBuilder.MAX_SUITS:
            raise NotEnoughCardsError("ERROR: Ran out of minor suits.")
        chosen_suits = random.sample(avail_suits, k=DeckBuilder.MAX_SUITS)

        # ensure major arcana that benefit other suits are not included in the selection
        exclusions = [v for k, v in self.affinity_majors.items() if k not in chosen_suits]
        avail_majors = self.__available_ranks_in_suit("Major Arcana", exclude=exclusions)
        if len(avail_majors) < DeckBuilder.MAX_MJR_ARCANA:
            raise NotEnoughCardsError("ERROR: Ran out of Major Arcana cards.")

        # add major arcana cards to the deck
        major_sample = random.sample(avail_majors, k=DeckBuilder.MAX_MJR_ARCANA)
        chosen_majors = []
        for c in major_sample:
            chosen_majors.append(self.__card_pick("Major Arcana", c))

        # add suit cards to the deck
        chosen_minors = []
        for s in chosen_suits:
            avail_minors = set(self.__available_ranks_in_suit(s))
            if len(avail_minors) < DeckBuilder.MAX_SUIT_CARDS:
                raise NotEnoughCardsError(f"ERROR: Ran out of {s} cards.")
            minor_sample = random.sample(avail_minors, k=DeckBuilder.MAX_SUIT_CARDS)
            for c in minor_sample:
                card = self.__card_pick(s, c)
                chosen_minors.append(card)

        deck = Deck(
            name=name,
            suits=chosen_suits,
            mjr_cards=chosen_majors,
            mnr_cards=chosen_minors
        )

        if len(deck) != DeckBuilder.TOTAL_DECK:
            raise NotEnoughCardsError(f"ERROR! {len(deck)} cards in the deck. Expecting {DeckBuilder.TOTAL_DECK}")

        return deck


if __name__ == '__main__':

    db = DeckBuilder()
    decks = []

    with open('decks.txt', 'w') as f:
        try:
            for i in range(NUM_DECKS):
                d = db.build_deck(i)
                decks.append(d)
                f.write(d.__repr__())

            # FIXME - NotEnoughCardsError thrown here
            # rebalanced = db.balance_decks(decks)
            # print(rebalanced)

        except Exception as e:
            logger.error(e)

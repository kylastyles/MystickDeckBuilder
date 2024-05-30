import itertools


class Deck:
    """
    A Deck is a collection of Cards. Its power is the sum of the Cards' powers.
    """
    def __init__(self, name="", suits=[], mjr_cards=[], mnr_cards=[]):
        self.Name = name
        self.Suits = suits
        self.Major_cards = mjr_cards
        self.Minor_cards = mnr_cards
        self.Power = self.calculate_power()

    def __repr__(self):
        return f"""
        Name: {self.Name}
        Suits: {self.Suits}
        Power: {self.Power}
        -------------------
        Cards: {self.Major_cards + self.Minor_cards}
        """

    def __len__(self):
        return len(self.Major_cards) + len(self.Minor_cards)

    def calculate_power(self):
        """
        Returns the sum of the Card powers in the Deck.
        """
        mjr_powers = [c.Power for c in self.Major_cards]
        mnr_powers = [c.Power for c in self.Minor_cards]

        return sum(mjr_powers + mnr_powers)


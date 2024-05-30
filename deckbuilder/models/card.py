

class Card:
    """
    A Card is the base object held within Decks.
    """
    def __init__(self, card_dict):
        self.ID = card_dict.get("ID")
        self.Type = card_dict.get("Type")
        self.Suit = card_dict.get("Suit")
        self.Rank = card_dict.get("Rank")
        self.Influence = card_dict.get("Influence")
        self.Name = card_dict.get("Name")
        self.Description = card_dict.get("Description")
        self.Copies = card_dict.get("Copies")
        self.OffensivePower = card_dict.get("OffensivePower")
        self.DefensivePower = card_dict.get("DefensivePower")
        self.GameAltering = card_dict.get("GameAltering")
        self.Power = self.calculate_power()

    def __repr__(self):
        return f"{self.ID}: {self.Name}"

    def calculate_power(self):
        """
        In the data file, there are three columns for power: Offensive, Defensive, and Game Altering.
        Based on its description, a card was assigned one point to one column.
        This algorithm gives more weight to Game Altering and Defensive cards.
        """
        try:
            o_power = int(self.OffensivePower)
        except ValueError:
            o_power = 0

        try:
            d_power = int(self.DefensivePower)
        except ValueError:
            d_power = 0

        try:
            ga_power = int(self.GameAltering)
        except ValueError:
            ga_power = 0

        return o_power + (2*d_power) + (3*ga_power)

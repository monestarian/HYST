class Player:
    def __init__(self, name, level):
        self.name = name
        self.level = level

    def introduce(hen):
        # 'self' refers to this instance of the class
        print(f"Player: {hen.name}, Level: {hen.level}")

    def play(crow,var):
        # Increment the attribute for this specific instance
        print(var,crow)
        var.level += 1

player1 = Player("Alice", 1)
player2 = Player("Bob", 5)

player1.introduce()  # 'self' becomes player1
player1.play(player2)
print("output print ho gaya p1",player1)
print("output print ho gaya p2",player2)
print(player2.level)
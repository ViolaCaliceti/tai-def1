import math
import random
import copy
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

# --- Constants ---
GRID_SIZE = 4
NEW_TILE_PROBABILITY_2 = 0.8
ALL_DIRECTIONS = ['up', 'down', 'left', 'right']

# --- Selenium Setup ---
try:
    driver = webdriver.Chrome()
    driver.get("file:///Users/francescoferrau/Desktop/AI/tai def1/index.html")
except Exception as e:
    print(f"Errore durante l'inizializzazione di Selenium: {e}")
    exit()

# --- Game Logic Functions ---
def move_and_merge_array_python(line_input):
    line = list(line_input)
    original_line = list(line_input)
    score_gained = 0
    temp_line = [val for val in line if val != 0]
    merged_line = []
    i = 0
    while i < len(temp_line):
        if i + 1 < len(temp_line) and temp_line[i] == temp_line[i+1]:
            merged_value = temp_line[i] * 2
            merged_line.append(merged_value)
            score_gained += merged_value
            i += 2
        else:
            merged_line.append(temp_line[i])
            i += 1
    new_line = merged_line + [0] * (GRID_SIZE - len(merged_line))
    moved_flag = (new_line != original_line)
    return new_line, score_gained, moved_flag

def _apply_slide_and_merge_only_python(board_input, direction):
    board = [list(row) for row in board_input]
    moved_overall = False
    total_score_gained = 0
    if direction == 'left':
        for r in range(GRID_SIZE):
            new_row, score, moved = move_and_merge_array_python(board[r])
            board[r] = new_row
            total_score_gained += score
            if moved: moved_overall = True
    elif direction == 'right':
        for r in range(GRID_SIZE):
            reversed_row = board[r][::-1]
            new_row_reversed, score, moved = move_and_merge_array_python(reversed_row)
            board[r] = new_row_reversed[::-1]
            total_score_gained += score
            if moved: moved_overall = True
    elif direction == 'up':
        for c in range(GRID_SIZE):
            column = [board[r][c] for r in range(GRID_SIZE)]
            new_column, score, moved = move_and_merge_array_python(column)
            total_score_gained += score
            if moved: moved_overall = True
            for r in range(GRID_SIZE):
                board[r][c] = new_column[r]
    elif direction == 'down':
        for c in range(GRID_SIZE):
            column = [board[r][c] for r in range(GRID_SIZE)][::-1]
            new_column_reversed, score, moved = move_and_merge_array_python(column)
            new_column = new_column_reversed[::-1]
            total_score_gained += score
            if moved: moved_overall = True
            for r in range(GRID_SIZE):
                board[r][c] = new_column[r]
    return board, total_score_gained, moved_overall

def _add_random_tile_python(board):
    empty_cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if board[r][c] == 0]
    if not empty_cells:
        return False
    r, c = random.choice(empty_cells)
    board[r][c] = 2 if random.random() < NEW_TILE_PROBABILITY_2 else 4
    return True

def apply_full_turn_python(board_input, direction):
    new_board, score_gained, moved = _apply_slide_and_merge_only_python(board_input, direction)
    if moved:
        _add_random_tile_python(new_board)
    return new_board, score_gained, moved

def is_game_over_python(board):
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 0:
                return False
            if c + 1 < GRID_SIZE and board[r][c+1] == board[r][c]:
                return False
            if r + 1 < GRID_SIZE and board[r+1][c] == board[r][c]:
                return False
    return True

# --- Selenium Interaction ---
def get_board_from_selenium(driver):
    board = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
    try:
        grid_cells_elements = driver.find_elements(By.CLASS_NAME, "grid")
        cell_index = 0
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if cell_index < len(grid_cells_elements):
                    value_str = grid_cells_elements[cell_index].get_attribute('data-value')
                    board[r][c] = int(value_str) if value_str else 0
                cell_index += 1
    except Exception as e:
        print(f"Errore durante la lettura della board da Selenium: {e}")
    return board

def make_move_selenium(driver, direction):
    try:
        direction_upper = direction.upper()
        driver.find_element(By.ID, f"move-{direction.lower()}").click()
        time.sleep(0.2)
    except Exception as e:
        print(f"Errore durante la mossa Selenium ({direction}): {e}")

def get_score_selenium(driver):
    try:
        return int(driver.find_element(By.ID, "score").text)
    except Exception as e:
        print(f"Errore nel leggere il punteggio: {e}")
        return 0

def is_game_over_selenium(driver):
    try:
        overlay = driver.find_element(By.ID, "game-over-message")
        return overlay.is_displayed()
    except Exception:
        return False

# --- MCTS AI ---
class MCTSNode:
    def __init__(self, board, score, move=None, parent=None):
        self.board = board
        self.score = score
        self.move = move
        self.parent = parent
        self.children = []
        self.visits = 0
        self.total_reward = 0

    def is_fully_expanded(self):
        return len(self.children) == len(get_valid_moves(self.board))

    def best_child(self, c_param=math.sqrt(2)):
        choices_weights = [
            (child.total_reward / child.visits) + c_param * math.sqrt(math.log(self.visits) / child.visits)
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]

def get_valid_moves(board):
    valid = []
    for move in ALL_DIRECTIONS:
        _, _, moved = _apply_slide_and_merge_only_python(board, move)
        if moved:
            valid.append(move)
    return valid

def expand_node(node):
    tried_moves = [child.move for child in node.children]
    untried_moves = [m for m in get_valid_moves(node.board) if m not in tried_moves]
    if not untried_moves:
        return node
    move = random.choice(untried_moves)
    new_board, score_gained, _ = apply_full_turn_python(copy.deepcopy(node.board), move)
    child_node = MCTSNode(new_board, node.score + score_gained, move=move, parent=node)
    node.children.append(child_node)
    return child_node

def simulate_from_node(node):
    board = copy.deepcopy(node.board)
    score = node.score
    while not is_game_over_python(board):
        valid_moves = get_valid_moves(board)
        if not valid_moves:
            break
        move = random.choice(valid_moves)
        board, gained, _ = apply_full_turn_python(board, move)
        score += gained
    return score

def backpropagate(node, reward):
    while node:
        node.visits += 1
        node.total_reward += reward
        node = node.parent

def choose_best_move_mcts(current_board, current_score, num_simulations):
    root = MCTSNode(current_board, current_score)
    for _ in range(num_simulations):
        node = root
        while node.is_fully_expanded() and node.children:
            node = node.best_child()
        if not node.is_fully_expanded():
            node = expand_node(node)
        reward = simulate_from_node(node)
        backpropagate(node, reward)
    if not root.children:
        return None
    return max(root.children, key=lambda c: c.total_reward / c.visits).move

# --- Main Game Loop ---
if __name__ == "__main__":
    NUM_SIMULATIONS = 100
    time.sleep(2)
    while True:
        if is_game_over_selenium(driver):
            print("Game Over (Selenium).")
            break
        current_board = get_board_from_selenium(driver)
        current_score = get_score_selenium(driver)
        if is_game_over_python(current_board):
            print("Game Over (logica Python).")
            break
        print("\nBoard attuale:")
        for row in current_board:
            print(row)
        best_move = choose_best_move_mcts(current_board, current_score, NUM_SIMULATIONS)
        if best_move:
            print(f"MCTS sceglie: {best_move.upper()}")
            make_move_selenium(driver, best_move)
        else:
            print("Nessuna mossa trovata. Uscita.")
            break
        time.sleep(0.3)
    input("Premi Invio per chiudere il browser...")
    driver.quit()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys # Importato per completezza, anche se i click sono usati
import time

# --- Configurazione Selenium ---
# Assicurati che chromedriver (o il driver per il tuo browser) sia nel tuo PATH
# o specifica il percorso esatto: webdriver.Chrome(executable_path='/path/to/chromedriver')
try:
    driver = webdriver.Chrome()
    # Modifica questo percorso se il tuo file index.html si trova altrove
    driver.get("file://C:/Users/viola/.openjfx/iCloudDrive/Uni - poli/TAI/tai def1 2/tai def1/index.html")
except Exception as e:
    print(f"Errore durante l'inizializzazione di Selenium: {e}")
    print("Assicurati che WebDriver sia installato e nel PATH, e che il percorso di index.html sia corretto.")
    exit()

# --- Cache per Memoization ---
memo = {}

# --- Logica del Gioco Replicata in Python ---

def move_and_merge_array_python(line):
    """
    Sposta e fonde i numeri in una singola riga o colonna.
    Restituisce la nuova linea, il punteggio ottenuto e un flag se qualcosa si è mosso.
    """
    original_line = list(line)
    score_gained = 0
    moved_flag = False

    # 1. Filtra gli zeri, mantenendo solo i numeri
    temp_line = [val for val in line if val != 0]

    # 2. Fonde i numeri adiacenti uguali
    merged_line = []
    i = 0
    while i < len(temp_line):
        if i + 1 < len(temp_line) and temp_line[i] == temp_line[i+1]:
            merged_value = temp_line[i] * 2
            merged_line.append(merged_value)
            score_gained += merged_value
            i += 2 # Salta il prossimo elemento poiché è stato fuso
        else:
            merged_line.append(temp_line[i])
            i += 1
    
    # 3. Riempie con zeri fino a raggiungere la lunghezza 4
    new_line = merged_line + [0] * (4 - len(merged_line))

    # Controlla se la linea è cambiata
    if new_line != original_line:
        moved_flag = True
            
    return new_line, score_gained, moved_flag

def simulate_move_python(board_input, direction):
    """
    Simula una mossa sulla board data e restituisce la nuova board,
    il punteggio ottenuto e un flag se qualcosa si è mosso.
    """
    board = [list(row) for row in board_input] # Crea una copia modificabile
    moved_overall = False
    total_score_gained = 0
    
    original_board_for_comparison = [list(row) for row in board_input]


    if direction == 'left':
        for r in range(4):
            new_row, score, moved = move_and_merge_array_python(board[r])
            board[r] = new_row
            total_score_gained += score
            if moved: moved_overall = True
    elif direction == 'right':
        for r in range(4):
            reversed_row = board[r][::-1]
            new_row_reversed, score, moved = move_and_merge_array_python(reversed_row)
            board[r] = new_row_reversed[::-1]
            total_score_gained += score
            if moved: moved_overall = True
    elif direction == 'up':
        for c in range(4):
            column = [board[r][c] for r in range(4)]
            new_column, score, moved = move_and_merge_array_python(column)
            total_score_gained += score
            if moved: moved_overall = True
            for r in range(4):
                board[r][c] = new_column[r]
    elif direction == 'down':
        for c in range(4):
            column = [board[r][c] for r in range(4)][::-1]
            new_column_reversed, score, moved = move_and_merge_array_python(column)
            new_column = new_column_reversed[::-1]
            total_score_gained += score
            if moved: moved_overall = True
            for r in range(4):
                board[r][c] = new_column[r]

    # A volte moved_overall potrebbe non essere impostato correttamente se le singole mosse
    # non lo impostano ma la board cambia. Un confronto finale assicura accuratezza.
    if not moved_overall:
         if board != original_board_for_comparison:
            moved_overall = True

    return board, total_score_gained, moved_overall

def get_empty_cells_python(board):
    """Restituisce una lista di tuple (riga, colonna) per tutte le celle vuote."""
    empty_cells = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                empty_cells.append((r, c))
    return empty_cells

def add_tile_python(board_input, position, value):
    """
    Aggiunge un tile alla board data in una posizione specifica.
    Restituisce una *nuova* board con il tile aggiunto.
    """
    board = [list(row) for row in board_input] # Crea una copia
    row, col = position
    if 0 <= row < 4 and 0 <= col < 4 and board[row][col] == 0:
        board[row][col] = value
    return board

def is_game_over_python(board):
    """Controlla se il gioco è finito (nessuna cella vuota e nessuna mossa possibile)."""
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                return False  # Trovata una cella vuota

    for r in range(4):
        for c in range(4):
            current_val = board[r][c]
            if c + 1 < 4 and board[r][c+1] == current_val: # Controlla a destra
                return False
            if r + 1 < 4 and board[r+1][c] == current_val: # Controlla in basso
                return False
    return True # Nessuna cella vuota e nessuna mossa possibile

# --- Funzioni di Interazione con Selenium ---

def get_board_from_selenium(driver_instance):
    """Legge lo stato attuale della board dal DOM."""
    board = [[0]*4 for _ in range(4)]
    try:
        grid_cells_elements = driver_instance.find_elements(By.CLASS_NAME, "grid")
        cell_index = 0
        for r in range(4):
            for c in range(4):
                if cell_index < len(grid_cells_elements):
                    value_str = grid_cells_elements[cell_index].get_attribute('data-value')
                    board[r][c] = int(value_str) if value_str else 0
                cell_index += 1
    except Exception as e:
        print(f"Errore durante la lettura della board da Selenium: {e}")
        # Potrebbe essere utile restituire uno stato di errore o lanciare l'eccezione
    return board

def make_move_selenium(driver_instance, direction_str):
    """Esegue una mossa nel browser cliccando i bottoni."""
    try:
        if direction_str == "UP":
            driver_instance.find_element(By.ID, "move-up").click()
        elif direction_str == "DOWN":
            driver_instance.find_element(By.ID, "move-down").click()
        elif direction_str == "LEFT":
            driver_instance.find_element(By.ID, "move-left").click()
        elif direction_str == "RIGHT":
            driver_instance.find_element(By.ID, "move-right").click()
        time.sleep(0.1)  # Pausa per permettere al gioco di aggiornarsi
    except Exception as e:
        print(f"Errore durante l'esecuzione della mossa con Selenium ({direction_str}): {e}")


def get_score_selenium(driver_instance):
    """Legge il punteggio attuale dal DOM."""
    try:
        return int(driver_instance.find_element(By.ID, "score").text)
    except Exception as e:
        print(f"Errore durante la lettura del punteggio da Selenium: {e}")
        return 0 # Valore di default in caso di errore

def is_game_over_selenium(driver_instance):
    """Controlla se il messaggio di game over è visualizzato nel DOM."""
    try:
        message_overlay = driver_instance.find_element(By.ID, "game-over-message")
        if message_overlay.is_displayed():
            message_text_element = driver_instance.find_element(By.ID, "message-text")
            if "Game Over" in message_text_element.text:
                return True
    except Exception: # Gestisce il caso in cui gli elementi non siano trovati (es. all'inizio)
        return False
    return False

# --- Algoritmo AI: Expectiminimax ed Euristica ---

def heuristic(board, current_game_score_from_sim):
    """
    Funzione euristica per valutare la bontà di una board.
    Punteggi più alti sono migliori.
    """
    empty_cells_count = len(get_empty_cells_python(board))
    
    # Monotonicità: pesi da 16 (in alto a sinistra) a 1 (in basso a destra)
    weight_matrix = [
        [16, 15, 14, 13],
        [12, 11, 10,  9],
        [ 8,  7,  6,  5],
        [ 4,  3,  2,  1]
    ]
    monotonicity_score = 0
    for r in range(4):
        for c in range(4):
            monotonicity_score += board[r][c] * weight_matrix[r][c]

    # Uniformità/Lisciatura (penalizza grandi differenze tra tile adiacenti)
    smoothness_score = 0

    # Nuovo termine: premia celle uguali adiacenti (orizzontali e verticali)
    adjacency_score = 0
    for r in range(4):
        for c in range(4):
            if c < 3 and board[r][c] != 0 and board[r][c] == board[r][c+1]:
                adjacency_score += board[r][c]
            if r < 3 and board[r][c] != 0 and board[r][c] == board[r+1][c]:
                adjacency_score += board[r][c]

    max_tile_value = 0
    for r in range(4):
        for c_val in board[r]:
            if c_val > max_tile_value:
                max_tile_value = c_val

    # Pesi per i componenti dell'euristica (da affinare!)
    w_score = 1.0
    w_empty = 250.0
    w_mono = 15.0
    w_smooth = 10.0
    w_max_tile = 20.0
    w_adjacent = 50.0  # Peso per il nuovo termine di adiacenza

    final_heuristic_score = (current_game_score_from_sim * w_score +
                             empty_cells_count * w_empty +
                             monotonicity_score * w_mono +
                             smoothness_score * w_smooth +
                             max_tile_value * w_max_tile +
                             adjacency_score * w_adjacent)
    return final_heuristic_score


def expectiminimax(board_state, depth, agent_is_player, current_sim_score):
    """
    Algoritmo Expectiminimax.
    - agent_is_player = True per il nostro turno (MAX), False per il turno del computer (CHANCE).
    - current_sim_score è il punteggio accumulato *durante questa specifica simulazione*.
    """
    board_tuple_key = tuple(map(tuple, board_state))
    memo_key = (board_tuple_key, depth, agent_is_player, current_sim_score)

    if memo_key in memo:
        return memo[memo_key]

    if is_game_over_python(board_state) or depth == 0:
        # L'euristica ora riceve il punteggio accumulato nella simulazione
        return heuristic(board_state, current_sim_score)

    final_value = 0

    if agent_is_player:  # MAX Node (Nostro turno)
        max_eval = -float('inf')
        any_move_possible = False
        for direction in ['up', 'down', 'left', 'right']:
            new_board, score_from_this_move, moved = simulate_move_python(board_state, direction)
            if moved:
                any_move_possible = True
                # Il punteggio per il prossimo stato include quello di questa mossa
                eval_score = expectiminimax(new_board, depth, False, current_sim_score + score_from_this_move)
                max_eval = max(max_eval, eval_score)
        
        # Se nessuna mossa è possibile, è come se il gioco fosse finito per questo ramo
        final_value = max_eval if any_move_possible else heuristic(board_state, current_sim_score)

    else:  # CHANCE Node (Turno del computer di aggiungere un tile)
        empty_cells = get_empty_cells_python(board_state)
        if not empty_cells: # Non dovremmo arrivare qui se is_game_over_python funziona bene
            final_value = heuristic(board_state, current_sim_score)
        else:
            expected_score_sum = 0
            num_empty_cells = len(empty_cells)
            
            prob_2_appears = 0.8 # Probabilità che appaia un 2
            prob_4_appears = 0.2 # Probabilità che appaia un 4

            for r_idx, c_idx in empty_cells:
                # Simula l'aggiunta di un '2'
                board_with_2 = add_tile_python(board_state, (r_idx, c_idx), 2)
                # Il punteggio della simulazione non cambia quando il computer aggiunge un tile
                expected_score_sum += (prob_2_appears / num_empty_cells) * expectiminimax(board_with_2, depth - 1, True, current_sim_score)
                
                # Simula l'aggiunta di un '4'
                board_with_4 = add_tile_python(board_state, (r_idx, c_idx), 4)
                expected_score_sum += (prob_4_appears / num_empty_cells) * expectiminimax(board_with_4, depth - 1, True, current_sim_score)
            
            final_value = expected_score_sum
    
    memo[memo_key] = final_value
    return final_value

def choose_best_move(board_state_from_game, search_depth, actual_game_score):
    """Sceglie la mossa migliore usando Expectiminimax."""
    best_score_found = -float('inf')
    best_move_direction = None
    
    possible_directions = ['up', 'down', 'left', 'right']
    
    print(f"Valutazione mosse con profondità {search_depth}:")
    for direction in possible_directions:
        # Simula la nostra mossa sulla board attuale del gioco
        sim_board_after_our_move, score_gained_by_our_move, moved = simulate_move_python(board_state_from_game, direction)
        
        if moved:
            # Ora, valuta questo stato (che è un nodo CHANCE)
            # Il punteggio passato a expectiminimax è quello attuale del gioco + quello della nostra mossa simulata
            current_eval = expectiminimax(sim_board_after_our_move, search_depth, False, actual_game_score + score_gained_by_our_move)
            print(f"  - Mossa: {direction:<5}, Punteggio atteso: {current_eval:.2f}")
            if current_eval > best_score_found:
                best_score_found = current_eval
                best_move_direction = direction
        else:
            print(f"  - Mossa: {direction:<5}, (Nessun cambiamento)")


    if best_move_direction is None: # Fallback se nessuna mossa migliora o tutte non fanno nulla
        print("Nessuna mossa trovata che migliori il punteggio atteso o cambi la board. Tentativo di fallback.")
        for direction_fallback in possible_directions:
            _, _, moved_fallback = simulate_move_python(board_state_from_game, direction_fallback)
            if moved_fallback:
                print(f"Fallback: scelta la prima mossa valida: {direction_fallback}")
                best_move_direction = direction_fallback 
                break
                
    return best_move_direction

# --- Loop Principale del Gioco ---
def auto_test(num_games=10, win_tile=2048):
    win_count = 0
    lose_count = 0
    max_tiles = []

    for game in range(num_games):
        print(f"\n--- Partita {game+1} ---")
        # Ricarica la pagina per resettare il gioco
        driver.refresh()
        time.sleep(2)
        memo.clear()
        max_tile = 0

        while True:
            if is_game_over_selenium(driver):
                print("Game Over rilevato da Selenium (messaggio nel DOM).")
                break

            current_board_selenium = get_board_from_selenium(driver)
            current_score_from_game = get_score_selenium(driver)

            # Controllo di game over anche con la logica Python interna
            if is_game_over_python(current_board_selenium):
                print("Game Over rilevato dalla logica Python interna.")
                break

            # Aggiorna il massimo tile trovato
            max_tile = max(max_tile, max([max(row) for row in current_board_selenium]))

            memo.clear()
            best_direction_to_move = choose_best_move(current_board_selenium, SEARCH_DEPTH, current_score_from_game)

            if best_direction_to_move:
                make_move_selenium(driver, best_direction_to_move.upper())
                time.sleep(0.2)
            else:
                # Fallback: tenta una mossa qualsiasi
                moved_in_fallback = False
                for fallback_move in ['up', 'down', 'left', 'right']:
                    _, _, did_move = simulate_move_python(current_board_selenium, fallback_move)
                    if did_move:
                        make_move_selenium(driver, fallback_move.upper())
                        moved_in_fallback = True
                        time.sleep(0.2)
                        break
                if not moved_in_fallback:
                    break

        print(f"Valore massimo raggiunto: {max_tile}")
        max_tiles.append(max_tile)
        if max_tile >= win_tile:
            win_count += 1
        else:
            lose_count += 1

    print("\n=== RISULTATI TEST AUTOMATICO ===")
    print(f"Partite vinte (tile >= {win_tile}): {win_count}/{num_games}")
    print(f"Partite perse: {lose_count}/{num_games}")
    print(f"Valori massimi raggiunti: {max_tiles}")
    print(f"Valore massimo assoluto: {max(max_tiles)}")

if __name__ == "__main__":
    try:
        SEARCH_DEPTH = 4
        auto_test(num_games=10, win_tile=2048)
    except Exception as e:
        print(f"Si è verificato un errore nel test automatico: {e}")
    finally:
        input("Premi Invio per chiudere il browser...")
        driver.quit()

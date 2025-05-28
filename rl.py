import numpy as np
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pickle
import os
from collections import deque
import matplotlib.pyplot as plt

class Game2048Environment:
    def __init__(self, headless=False):
        """
        Inizializza l'ambiente di gioco.
        
        Args:
            headless: Se True, il browser non sarà visibile (utile per training veloce)
        """
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        
        # Ottimizzazioni per velocizzare Selenium
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        # IMPORTANTE: Modifica questo percorso con il tuo
        # Usa il formato file:// per accedere a file locali
        self.driver.get('file:///Users/francescoferrau/Desktop/AI/tai%20def1/index.html')
        
        # Aspetta che il gioco sia completamente caricato
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "grid"))
        )
        
        self.actions = ['up', 'down', 'left', 'right']
        self.key_mapping = {
            'up': Keys.ARROW_UP,
            'down': Keys.ARROW_DOWN,
            'left': Keys.ARROW_LEFT,
            'right': Keys.ARROW_RIGHT
        }
        self.highest_tile_ever = 0
        self.game_over = False
        self.win_detected = False
        self.move_count = 0

    def get_state(self):
        """Ottiene lo stato corrente della griglia."""
        grid = []
        cells = self.driver.find_elements(By.CLASS_NAME, 'grid')
        for cell in cells:
            value = cell.get_attribute('data-value')
            grid.append(int(value) if value and value.isdigit() else 0)
        return np.array(grid).reshape(4, 4)

    def get_score(self):
        """Ottiene il punteggio corrente."""
        score_element = self.driver.find_element(By.ID, 'score')
        return int(score_element.text)
    
    def get_empty_cells_count(self):
        """Conta il numero di celle vuote (utile per la valutazione)."""
        state = self.get_state()
        return np.sum(state == 0)
    
    def check_game_over_or_win(self):
        """Controlla se il gioco è terminato o se abbiamo vinto."""
        try:
            overlay = self.driver.find_element(By.ID, 'game-over-message')
            if overlay.is_displayed():
                message = self.driver.find_element(By.ID, 'message-text').text
                if "Game Over" in message:
                    return "game_over"
                elif "2048" in message and not self.win_detected:
                    # Clicca su "Continue" per continuare dopo 2048
                    continue_button = self.driver.find_element(By.ID, 'new-game-message-button')
                    continue_button.click()
                    time.sleep(0.1)
                    return "win"
        except:
            pass
        return None

    def make_move(self, action):
        """
        Esegue una mossa e calcola la ricompensa.
        
        Returns:
            tuple: (new_state, reward, done, info)
        """
        old_state = self.get_state()
        old_score = self.get_score()
        old_empty = self.get_empty_cells_count()
        old_highest = np.max(old_state)
        
        # Esegui la mossa
        self.driver.find_element(By.TAG_NAME, 'body').send_keys(self.key_mapping[action])
        time.sleep(0.1)  # Ridotto per velocizzare il training
        
        # Controlla lo stato del gioco
        status = self.check_game_over_or_win()
        if status == "game_over":
            self.game_over = True
        elif status == "win":
            self.win_detected = True
        
        new_state = self.get_state()
        new_score = self.get_score()
        new_empty = self.get_empty_cells_count()
        new_highest = np.max(new_state)
        
        # Aggiorna statistiche
        if new_highest > self.highest_tile_ever:
            self.highest_tile_ever = new_highest
        
        # Sistema di ricompense migliorato
        reward = 0
        
        # 1. Ricompensa base per l'aumento di punteggio
        score_increase = new_score - old_score
        if score_increase > 0:
            # Ricompensa logaritmica per evitare che punteggi alti dominino
            reward += np.log2(score_increase + 1) * 10
        
        # 2. Bonus per aver creato un tile più alto
        if new_highest > old_highest:
            # Ricompensa esponenziale per incentivare tiles alti
            reward += (2 ** (np.log2(new_highest) - 3)) * 10
            
            # Super bonus per milestones importanti
            if new_highest == 2048:
                reward += 5000
            elif new_highest == 4096:
                reward += 10000
            elif new_highest == 8192:
                reward += 20000
        
        # 3. Ricompensa per mantenere celle vuote (importante per la sopravvivenza)
        empty_cells_reward = new_empty * 5
        reward += empty_cells_reward
        
        # 4. Bonus per mantenere il tile più alto in un angolo
        corners = [new_state[0, 0], new_state[0, 3], new_state[3, 0], new_state[3, 3]]
        if new_highest in corners and new_highest >= 128:
            reward += np.log2(new_highest) * 20
            
            # Extra bonus se è nell'angolo in alto a sinistra (strategia comune)
            if new_state[0, 0] == new_highest:
                reward += np.log2(new_highest) * 10
        
        # 5. Penalità per mosse invalide
        state_changed = not np.array_equal(old_state, new_state)
        if not state_changed:
            reward -= 50
        
        # 6. Penalità per perdere celle vuote
        if new_empty < old_empty:
            reward -= (old_empty - new_empty) * 3
        
        # 7. Penalità severa per game over
        if self.game_over:
            reward -= 2000
        
        # Incrementa il contatore di mosse
        if state_changed:
            self.move_count += 1
        
        # Informazioni aggiuntive per il debug
        info = {
            'score': new_score,
            'highest_tile': new_highest,
            'empty_cells': new_empty,
            'move_count': self.move_count,
            'valid_move': state_changed
        }
        
        done = self.game_over
        
        return new_state, reward, done, info

    def reset(self):
        """Resetta il gioco per un nuovo episodio."""
        try:
            # Gestisci l'overlay se presente
            overlay = self.driver.find_element(By.ID, 'game-over-message')
            if overlay.is_displayed():
                new_game_button = self.driver.find_element(By.ID, 'new-game-message-button')
                new_game_button.click()
            else:
                self.driver.find_element(By.ID, 'new-game-button').click()
        except:
            self.driver.find_element(By.ID, 'new-game-button').click()
        
        time.sleep(0.2)
        self.game_over = False
        self.win_detected = False
        self.move_count = 0
        return self.get_state()
    
    def close(self):
        """Chiude il browser."""
        self.driver.quit()


class ImprovedQLearningAgent:
    def __init__(self, actions, load_file=None):
        """
        Q-Learning agent migliorato con tecniche avanzate.
        """
        self.actions = actions
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.3  # Esplorazione iniziale alta
        self.epsilon_decay = 0.9997
        self.min_epsilon = 0.01
        
        # Q-table con valori di default
        self.q_table = {}
        self.default_q_value = 0
        
        # Experience replay buffer
        self.experience_buffer = deque(maxlen=5000)
        
        # Statistiche per il monitoraggio
        self.episode_rewards = []
        self.episode_scores = []
        self.episode_highest_tiles = []
        
        # Carica Q-table se disponibile
        if load_file and os.path.exists(load_file):
            with open(load_file, 'rb') as f:
                saved_data = pickle.load(f)
                self.q_table = saved_data.get('q_table', {})
                self.epsilon = saved_data.get('epsilon', self.epsilon)
                print(f"Caricata Q-table con {len(self.q_table)} stati")
                print(f"Epsilon corrente: {self.epsilon:.4f}")

    def get_state_key(self, state):
        """
        Crea una rappresentazione efficiente dello stato.
        Usa pattern recognition per identificare configurazioni simili.
        """
        # Normalizza i valori usando log2 per ridurre la dimensionalità
        normalized = np.zeros_like(state)
        non_zero_mask = state > 0
        normalized[non_zero_mask] = np.log2(state[non_zero_mask])
        
        # Feature 1: Posizione dei 4 tiles più alti
        flat_state = normalized.flatten()
        top_indices = np.argsort(flat_state)[-4:]
        top_positions = tuple(sorted([(idx, int(flat_state[idx])) for idx in top_indices if flat_state[idx] > 0]))
        
        # Feature 2: Pattern della griglia (monotonia)
        monotonicity_h = 0
        monotonicity_v = 0
        
        for i in range(4):
            # Monotonia orizzontale
            row = normalized[i, :]
            if all(row[j] <= row[j+1] for j in range(3)):
                monotonicity_h += 1
            elif all(row[j] >= row[j+1] for j in range(3)):
                monotonicity_h += 1
                
            # Monotonia verticale
            col = normalized[:, i]
            if all(col[j] <= col[j+1] for j in range(3)):
                monotonicity_v += 1
            elif all(col[j] >= col[j+1] for j in range(3)):
                monotonicity_v += 1
        
        # Feature 3: Distribuzione dei valori
        unique, counts = np.unique(normalized[normalized > 0], return_counts=True)
        value_distribution = tuple(zip(unique.astype(int), counts))
        
        # Combina tutte le features
        state_key = (
            top_positions,
            monotonicity_h,
            monotonicity_v,
            value_distribution,
            np.sum(state == 0)  # Numero di celle vuote
        )
        
        return state_key

    def get_q_value(self, state, action):
        """Ottiene il valore Q per uno stato-azione."""
        state_key = self.get_state_key(state)
        if state_key not in self.q_table:
            self.q_table[state_key] = {a: self.default_q_value for a in self.actions}
        return self.q_table[state_key].get(action, self.default_q_value)

    def get_action(self, state, training=True):
        """
        Seleziona un'azione usando epsilon-greedy policy.
        
        Args:
            state: Stato corrente del gioco
            training: Se False, usa sempre la migliore azione (no esplorazione)
        """
        # Durante il test, usa sempre la migliore azione
        if not training:
            state_key = self.get_state_key(state)
            if state_key in self.q_table:
                return max(self.q_table[state_key].items(), key=lambda x: x[1])[0]
            else:
                return random.choice(self.actions)
        
        # Epsilon-greedy durante il training
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        
        # Scegli l'azione con il valore Q più alto
        state_key = self.get_state_key(state)
        if state_key not in self.q_table:
            self.q_table[state_key] = {a: self.default_q_value for a in self.actions}
        
        # Aggiungi un po' di rumore per rompere i pareggi
        q_values = self.q_table[state_key]
        best_value = max(q_values.values())
        best_actions = [a for a, v in q_values.items() if v == best_value]
        
        return random.choice(best_actions)

    def learn(self, state, action, reward, next_state, done):
        """
        Aggiorna la Q-table usando l'equazione di Q-learning.
        """
        state_key = self.get_state_key(state)
        next_state_key = self.get_state_key(next_state)
        
        # Inizializza gli stati se non esistono
        if state_key not in self.q_table:
            self.q_table[state_key] = {a: self.default_q_value for a in self.actions}
        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = {a: self.default_q_value for a in self.actions}
        
        # Q-learning update
        current_q = self.q_table[state_key][action]
        
        if done:
            target = reward
        else:
            next_max_q = max(self.q_table[next_state_key].values())
            target = reward + self.discount_factor * next_max_q
        
        # Update con learning rate
        new_q = current_q + self.learning_rate * (target - current_q)
        self.q_table[state_key][action] = new_q

    def add_experience(self, state, action, reward, next_state, done):
        """Aggiunge un'esperienza al buffer per il replay."""
        self.experience_buffer.append((state, action, reward, next_state, done))

    def replay_experience(self, batch_size=32):
        """
        Experience replay: riapprende da esperienze passate casuali.
        Questo aiuta a rompere le correlazioni temporali.
        """
        if len(self.experience_buffer) < batch_size:
            return
        
        # Campiona un batch casuale di esperienze
        batch = random.sample(self.experience_buffer, batch_size)
        
        for state, action, reward, next_state, done in batch:
            self.learn(state, action, reward, next_state, done)

    def decay_epsilon(self):
        """Riduce epsilon per diminuire l'esplorazione nel tempo."""
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

    def save(self, filename):
        """Salva l'agent (Q-table + parametri)."""
        save_data = {
            'q_table': self.q_table,
            'epsilon': self.epsilon,
            'episode_rewards': self.episode_rewards,
            'episode_scores': self.episode_scores,
            'episode_highest_tiles': self.episode_highest_tiles
        }
        with open(filename, 'wb') as f:
            pickle.dump(save_data, f)
        print(f"Agent salvato in {filename} ({len(self.q_table)} stati)")

    def plot_statistics(self, save_path='training_stats.png'):
        """Crea grafici delle statistiche di training."""
        if len(self.episode_scores) < 2:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Punteggi
        axes[0, 0].plot(self.episode_scores)
        axes[0, 0].set_title('Punteggio per Episodio')
        axes[0, 0].set_xlabel('Episodio')
        axes[0, 0].set_ylabel('Punteggio')
        
        # Tile più alto
        axes[0, 1].plot(self.episode_highest_tiles)
        axes[0, 1].set_title('Tile Più Alto per Episodio')
        axes[0, 1].set_xlabel('Episodio')
        axes[0, 1].set_ylabel('Valore Tile')
        axes[0, 1].set_yscale('log', base=2)
        
        # Ricompense totali
        axes[1, 0].plot(self.episode_rewards)
        axes[1, 0].set_title('Ricompensa Totale per Episodio')
        axes[1, 0].set_xlabel('Episodio')
        axes[1, 0].set_ylabel('Ricompensa')
        
        # Media mobile dei punteggi
        window_size = min(100, len(self.episode_scores) // 4)
        if window_size > 1:
            moving_avg = np.convolve(self.episode_scores, 
                                     np.ones(window_size)/window_size, 
                                     mode='valid')
            axes[1, 1].plot(moving_avg)
            axes[1, 1].set_title(f'Media Mobile Punteggi (finestra={window_size})')
            axes[1, 1].set_xlabel('Episodio')
            axes[1, 1].set_ylabel('Punteggio Medio')
        
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()


def train_agent(episodes=1000, save_interval=50, headless=False):
    """
    Funzione principale di training con monitoraggio avanzato.
    """
    print("Inizializzazione ambiente e agent...")
    env = Game2048Environment(headless=headless)
    agent = ImprovedQLearningAgent(['up', 'down', 'left', 'right'], 'q_table_2048.pkl')
    
    # Statistiche globali
    best_score_ever = 0
    best_tile_ever = 0
    total_wins = 0
    total_4096 = 0
    total_8192 = 0
    
    print(f"Inizio training per {episodes} episodi...")
    print("=" * 60)
    
    for episode in range(episodes):
        state = env.reset()
        episode_reward = 0
        moves = 0
        invalid_moves = 0
        
        # Episodio di gioco
        while True:
            # Scegli e esegui azione
            action = agent.get_action(state, training=True)
            next_state, reward, done, info = env.make_move(action)
            
            # Traccia mosse invalide
            if not info['valid_move']:
                invalid_moves += 1
                if invalid_moves > 10:  # Tropppe mosse invalide, termina
                    done = True
            else:
                invalid_moves = 0
                moves += 1
            
            # Apprendimento
            agent.add_experience(state, action, reward, next_state, done)
            agent.learn(state, action, reward, next_state, done)
            
            # Experience replay ogni 10 mosse
            if moves % 10 == 0:
                agent.replay_experience(batch_size=64)
            
            episode_reward += reward
            state = next_state
            
            if done or moves > 5000:  # Limite di sicurezza
                break
        
        # Aggiorna statistiche
        final_score = info['score']
        highest_tile = info['highest_tile']
        
        agent.episode_rewards.append(episode_reward)
        agent.episode_scores.append(final_score)
        agent.episode_highest_tiles.append(highest_tile)
        
        # Aggiorna record
        if final_score > best_score_ever:
            best_score_ever = final_score
        if highest_tile > best_tile_ever:
            best_tile_ever = highest_tile
        
        # Conta achievements
        if highest_tile >= 2048:
            total_wins += 1
        if highest_tile >= 4096:
            total_4096 += 1
        if highest_tile >= 8192:
            total_8192 += 1
        
        # Decay epsilon
        agent.decay_epsilon()
        
        # Report periodico
        if (episode + 1) % 10 == 0:
            recent_scores = agent.episode_scores[-10:]
            avg_score = np.mean(recent_scores)
            
            print(f"\nEpisodio {episode + 1}/{episodes}")
            print(f"  Punteggio: {final_score:,} | Media ultimi 10: {avg_score:,.0f}")
            print(f"  Tile più alto: {highest_tile} | Mosse: {moves}")
            print(f"  Ricompensa episodio: {episode_reward:.1f}")
            print(f"  Epsilon: {agent.epsilon:.4f} | Stati Q-table: {len(agent.q_table):,}")
            print(f"  Record - Punteggio: {best_score_ever:,} | Tile: {best_tile_ever}")
            print(f"  Vittorie (≥2048): {total_wins} | ≥4096: {total_4096} | ≥8192: {total_8192}")
            print("-" * 60)
        
        # Salvataggio periodico
        if (episode + 1) % save_interval == 0:
            agent.save(f'q_table_2048_ep{episode+1}.pkl')
            agent.save('q_table_2048.pkl')  # Salva anche come file principale
            agent.plot_statistics(f'training_stats_ep{episode+1}.png')
            print(f"✓ Checkpoint salvato all'episodio {episode + 1}")
    
    # Salvataggio finale
    print("\n" + "=" * 60)
    print("TRAINING COMPLETATO!")
    print(f"Miglior punteggio: {best_score_ever:,}")
    print(f"Miglior tile: {best_tile_ever}")
    print(f"Percentuale vittorie: {(total_wins/episodes)*100:.1f}%")
    
    agent.save('q_table_2048_final.pkl')
    agent.plot_statistics('training_stats_final.png')
    
    # Chiudi l'ambiente
    env.close()
    
    return agent


def test_agent(agent, num_games=10, delay=0.5):
    """
    Testa l'agent addestrato visualizzando il gioco.
    """
    print("\nTEST DELL'AGENT ADDESTRATO")
    print("=" * 40)
    
    env = Game2048Environment(headless=False)  # Mostra il browser
    
    scores = []
    tiles = []
    
    for game in range(num_games):
        print(f"\nPartita {game + 1}/{num_games}")
        state = env.reset()
        moves = 0
        
        while True:
            # Usa l'agent senza esplorazione (training=False)
            action = agent.get_action(state, training=False)
            next_state, _, done, info = env.make_move(action)
            
            if info['valid_move']:
                moves += 1
                time.sleep(delay)  # Pausa per vedere le mosse
            
            state = next_state
            
            if done:
                break
        
        final_score = info['score']
        highest_tile = info['highest_tile']
        
        scores.append(final_score)
        tiles.append(highest_tile)
        
        print(f"  Punteggio: {final_score:,}")
        print(f"  Tile più alto: {highest_tile}")
        print(f"  Mosse totali: {moves}")
    
    print("\n" + "=" * 40)
    print("RISULTATI TEST:")
    print(f"Punteggio medio: {np.mean(scores):,.0f}")
    print(f"Punteggio massimo: {max(scores):,}")
    print(f"Tile più alto raggiunto: {max(tiles)}")
    
    env.close()


if __name__ == "__main__":
    # Opzioni di training
    TRAIN_EPISODES = 5000
    SAVE_INTERVAL = 100
    HEADLESS = True  # Modifica da True a False per vedere il training
    
    # Training
    print("AVVIO Q-LEARNING PER 2048")
    print("Questo processo potrebbe richiedere diverse ore...\n")
    
    agent = train_agent(
        episodes=TRAIN_EPISODES,
        save_interval=SAVE_INTERVAL,
        headless=HEADLESS
    )
    
    # Test finale
    response = input("\nVuoi testare l'agent addestrato? (s/n): ")
    if response.lower() == 's':
        test_agent(agent, num_games=5, delay=0.3)
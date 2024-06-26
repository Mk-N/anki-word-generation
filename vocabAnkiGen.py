import os
import requests
import time
import concurrent.futures
import csv
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist
from threading import Lock

# Download NLTK data files (you need to do this once)
nltk.download('punkt')
nltk.download('stopwords')

# Rate limit settings
REQUESTS_PER_MINUTE = 60
DELAY_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE
rate_limit_lock = Lock()
last_request_time = 0

def rate_limited_request(url):
	global last_request_time

	while True:
		try:
			with rate_limit_lock:
				current_time = time.time()
				if current_time - last_request_time < DELAY_BETWEEN_REQUESTS:
					time.sleep(DELAY_BETWEEN_REQUESTS - (current_time - last_request_time))
				last_request_time = time.time()
				response = requests.get(url)

			if response.status_code == 200:
				return response.json()
			elif response.status_code == 429:
				print("Rate limit exceeded, waiting before retrying...")
				time.sleep(DELAY_BETWEEN_REQUESTS)
			else:
				return None
		except requests.exceptions.RequestException as e:
			print(f"Request failed: {e}, retrying...")
			time.sleep(DELAY_BETWEEN_REQUESTS)

def get_random_words(length):
	url = f"https://random-word-api.herokuapp.com/word?number={length}"
	return rate_limited_request(url)

def get_word_definition(word):
	url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
	return rate_limited_request(url)

def generate_hint(definition):
	stop_words = set(stopwords.words('english'))
	word_tokens = word_tokenize(definition.lower())
	filtered_tokens = [w for w in word_tokens if not w in stop_words and w.isalpha()]
	freq_dist = FreqDist(filtered_tokens)
	most_common = freq_dist.most_common()

	# Ensure fewer hint words than words in the definition and cap at 3
	hint_words = []
	num_words_in_definition = len(filtered_tokens)
	for word, freq in most_common:
		if len(hint_words) < min(num_words_in_definition - 1, 3):
			hint_words.append(word)
		else:
			break

	return "(" + ", ".join(hint_words) + ")"

def save_to_file(content, csv_content):
	output_dir = 'output'
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)

	text_file_path = os.path.join(output_dir, 'random_words_definitions.txt')
	with open(text_file_path, 'w') as file:
		file.write(content)

	csv_file_path = os.path.join(output_dir, 'random_words_definitions.csv')
	with open(csv_file_path, 'w', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(["Word Name", "Word Type", "Definition", "Hint"])
		writer.writerows(csv_content)

def main():
	num_words = int(input("Enter the number of random words: "))
	collected_words = set()
	output_content = ""
	csv_content = []
	remaining_words = num_words

	while remaining_words > 0:
		random_words = get_random_words(remaining_words)
		with concurrent.futures.ThreadPoolExecutor(max_workers=min(1000, remaining_words)) as executor:
			futures = {executor.submit(get_word_definition, word): word for word in random_words}
			for future in concurrent.futures.as_completed(futures):
				word = futures[future]
				definitions = future.result()
				if definitions:
					collected_words.add(word)
					output_content += f"\nWord: {word}\n"
					for meaning in definitions[0].get('meanings', []):
						part_of_speech = meaning.get('partOfSpeech')
						output_content += f"\nType: {part_of_speech.capitalize()}\n"

						for definition in meaning.get('definitions', []):
							definition_text = definition.get('definition')
							example = definition.get('example')
							hint = generate_hint(definition_text)
							if example:
								output_content += f"Definition: {definition_text}\nExample: {example}\n"
							else:
								output_content += f"Definition: {definition_text}\n"
							csv_content.append([word, part_of_speech.capitalize(), definition_text, hint])
				else:
					print(f"No definition found for word: {word}")

		remaining_words = num_words - len(collected_words)

	if output_content:
		save_to_file(output_content, csv_content)
		print(f"Definitions have been saved to 'output/random_words_definitions.txt' and 'output/random_words_definitions.csv'. Total words collected: {len(collected_words)}")
	else:
		print("No valid definitions were found.")

if __name__ == "__main__":
	main()

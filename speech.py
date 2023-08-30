import contextlib
import sys
import wave
import webrtcvad
import pyaudio
import os
import time
import datetime
import threading
import openai
import deepl
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import shutil
import sounddevice
from gtts import gTTS
from tkinter import filedialog
import sounddevice, os
from gtts import gTTS
import soundfile as sf
import numpy as np
from scipy.signal import resample


class CustomOutput:
    def __init__(self):
        self.text_widgets = []
        # self.main_text_widget = main_text_widget
        # self.original_stdout = sys.stdout  # 標準出力を保存

    def register(self, text_widget):
        self.text_widgets.append(text_widget)

    def write(self, string):
        for widget in self.text_widgets:
            widget.insert(tk.END, string)
            widget.see(tk.END)
        self.flush()

    def flush(self):
        for widget in self.text_widgets:
            widget.update_idletasks()

class MyApplication:
    def __init__(self):
        self.clear_output_folder()
        self.selected_input_device = None
        self.selected_output_device = None
        self.selected_language = 'English to Japanese'
        self.load_api()
        self.load_audio_setting()
        self.audio_dir = None
        self.is_exit = False
        self.is_enabled = True
        self.app = tk.Tk()
        self.app.title("RVT")
        self.app.iconbitmap('RVT.ico')
        self.app.geometry("350x300")
        self.app.configure(bg="black")

        # タブコンテナの作成
        self.notebook = ttk.Notebook(self.app)
        self.notebook.pack(expand=1, fill='both')

        style = ttk.Style()
        style.theme_create("MyStyle", parent="alt", settings={
            "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0], "background": "#333333"}},
            "TNotebook.Tab": {
                "configure": {"padding": [5, 1], "background": "#333333"},
                "map": {"background": [("selected", "#555555")]}
            }
        })
        style.theme_use("MyStyle")

        # メイン画面タブ
        self.main_frame = tk.Frame(self.notebook, bg="#333333")
        self.notebook.add(self.main_frame, text="main")

        # 設定画面タブ
        self.settings_frame = tk.Frame(self.notebook, bg="#333333")
        self.notebook.add(self.settings_frame, text="setting")

        # audio画面タブ
        self.audio_frame = tk.Frame(self.notebook, bg="#333333")
        self.notebook.add(self.audio_frame, text="audio")

        # 言語選択画面タブ
        self.translate_language_frame = tk.Frame(self.notebook, bg="#333333")
        self.notebook.add(self.translate_language_frame, text="language")

        # ファイル受付画面タブ
        self.input_file_frame = tk.Frame(self.notebook, bg="#333333")
        self.notebook.add(self.input_file_frame, text='file')

        # メイン画面のコンテンツ
        self.on_button = ctk.CTkButton(master=self.main_frame, text="ON", command=lambda: self.toggle_enabled(True))
        self.on_button.place(relx=0.3, rely=0.25, anchor=ctk.CENTER)
        self.off_button = ctk.CTkButton(master=self.main_frame, text="OFF", command=lambda: self.toggle_enabled(False))
        self.off_button.place(relx=0.7, rely=0.25, anchor=ctk.CENTER)
        self.exit_button = ctk.CTkButton(master=self.main_frame, text="exit", command=self.exit_app, bg_color="red")
        self.exit_button.place(relx=0.5, rely=0.4, anchor=ctk.CENTER)
        self.main_log_text = tk.Text(self.main_frame, bg="#333333", fg="white", height=10)
        self.main_log_text.pack(side=tk.BOTTOM, fill='x')

        # 設定画面のコンテンツ
        self.openai_label = tk.Label(self.settings_frame, text="RVT_OPENAI_API_KEY: ", bg="#333333", fg="white")
        self.openai_label.grid(row=0, column=0)
        self.openai_entry = tk.Entry(self.settings_frame, width=35)
        self.openai_entry.grid(row=0, column=1)
        self.openai_entry.insert(0, self.RVT_OPENAI_API_KEY)
        self.deepl_label = tk.Label(self.settings_frame, text="RVT_DEEPL_API_KEY: ", bg="#333333", fg="white")
        self.deepl_label.grid(row=1, column=0)
        self.deepl_entry = tk.Entry(self.settings_frame, width=35)
        self.deepl_entry.grid(row=1, column=1)
        self.deepl_entry.insert(0, self.RVT_DEEPL_API_KEY) 
        self.save_button = tk.Button(self.settings_frame, text="save", command=self.save_api_settings, bg="#555555", fg="white")
        self.save_button.grid(row=3, column=1)

        # audio画面のコンテンツ
        self.input_device_label = tk.Label(self.audio_frame, text="Input Device: ", bg="#333333", fg="white")
        self.input_device_label.grid(row=0, column=0)
        self.input_device_combobox = ttk.Combobox(self.audio_frame, values=[device['name'] for device in sounddevice.query_devices()], width=35)
        self.input_device_combobox.grid(row=0, column=1)
        device_list = [device['name'] for device in sounddevice.query_devices()]
        try:
            default_index = device_list.index(self.selected_input_device)
        except ValueError:
            default_index = 0 
        self.input_device_combobox.current(default_index)

        default_input_device_index = sounddevice.default.device[0]
        self.input_device_combobox.current(default_input_device_index)

        # 出力デバイスの選択
        self.output_device_label = tk.Label(self.audio_frame, text="Output Device: ", bg="#333333", fg="white")
        self.output_device_label.grid(row=1, column=0)
        self.output_device_combobox = ttk.Combobox(self.audio_frame, values=[device['name'] for device in sounddevice.query_devices()], width=35)
        self.output_device_combobox.grid(row=1, column=1)
        output_device_name = 'CABLE Input (VB-Audio Virtual C'
        device_names = [device['name'] for device in sounddevice.query_devices()]

        # デバイス名が存在するか確認
        if output_device_name in device_names:
            output_device_index = device_names.index(output_device_name)
            self.output_device_combobox.current(output_device_index)
        else:
            print(f"Warning: Device '{output_device_name}' not found. Default device will be used.")

        # audio保存ボタン
        self.audio_save_button = tk.Button(self.audio_frame, text="save", command=self.save_audio_settings, bg="#555555", fg="white")
        self.audio_save_button.grid(row=2, column=1)

        # 言語設定のコンテンツ
        self.language_label = tk.Label(self.translate_language_frame, text="Language: ", bg="#333333", fg="white")
        self.language_label.grid(row=0, column=0)
        self.language_combobox_lang = ttk.Combobox(self.translate_language_frame, values=['English to Japanese', 'Japanese to English'], width=35)
        self.language_combobox_lang.grid(row=0, column=1)
        self.language_combobox_lang.current(0)
        self.language_save_button = tk.Button(self.translate_language_frame, text="save", command=self.save_translate_language_lang, bg="#555555", fg="white")
        self.language_save_button.grid(row=1, column=1)
        # ファイル設定のコンテンツ
        self.input_label = tk.Label(self.input_file_frame, text="Input File: ", bg='#333333', fg="white")
        self.input_label.place(x=0, y=0)
        self.file_entry = tk.Entry(self.input_file_frame, width=20)
        self.file_entry.place(x=100, y=0)
        self.file_button = tk.Button(self.input_file_frame, text="Browse", command=self.select_audio_file)
        self.file_button.place(x=250, y=0)
        # 言語選択ボタン
        self.language_label_input = tk.Label(self.input_file_frame, text="Language: ", bg="#333333", fg="white")
        self.language_label_input.place(x=0, y=60)
        self.language_combobox_input = ttk.Combobox(self.input_file_frame, values=['English to Japanese', 'Japanese to English'], width=15)
        self.language_combobox_input.place(x=100, y=60)
        self.language_combobox_input.current(0)
        self.language_save_button_input = tk.Button(self.input_file_frame, text="save", command=self.save_translate_language_input, bg="#555555", fg="white")
        self.language_save_button_input.place(x=250, y=60)

        self.start_button = tk.Button(self.input_file_frame, text="start", command=self.start_file)
        self.start_button.place(x=100, y=90)

        self.file_tab_log_text = tk.Text(self.input_file_frame, bg="#333333", fg="white", height=10)
        self.file_tab_log_text.pack(side=tk.BOTTOM, fill='x')

        custom_output = CustomOutput()
        custom_output.register(self.main_log_text)
        custom_output.register(self.file_tab_log_text)

        sys.stdout = custom_output
        sys.stderr = custom_output
        self.notebook.pack()

        # 音声処理のスレッドを開始
        self.audio_thread = threading.Thread(target=self.start_audio_processing)
        self.audio_thread.start()

        self.app.mainloop()

    def clear_output_folder(self):
        output_folder = 'output'
        if not os.path.exists(output_folder):
            print(f"{output_folder} does not exist.")
            return
        for filename in os.listdir(output_folder):
            file_path = os.path.join(output_folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    for root, dirs, files in os.walk(file_path, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")

    def load_api(self):
        load_dotenv()
        self.RVT_OPENAI_API_KEY = os.getenv('RVT_OPENAI_API_KEY', '')
        self.RVT_DEEPL_API_KEY = os.getenv('RVT_DEEPL_API_KEY', '')
        if not self.RVT_OPENAI_API_KEY:
            print("OpenAI API key is not set. Please set in Settings tab")
        if not self.RVT_DEEPL_API_KEY:
            print("DeepL API key is not set. Please set in Settings tab")
        openai.api_key = self.RVT_OPENAI_API_KEY
    
    def load_audio_setting(self):
        try:
            with open('audio_settings.key', 'r', encoding='utf-8') as file:
                lines = file.readlines()
                self.selected_input_device = lines[0].strip()
                self.selected_output_device = lines[1].strip()
        except FileNotFoundError:
            print("Audio settings not found.")
            self.selected_input_device = None
            self.selected_output_device = None

    def save_api_settings(self):
        if not os.path.exists('.env'):
            with open('.env', 'w', encoding='utf-8') as f:
                f.write("RVT_OPENAI_API_KEY=\n")
                f.write("RVT_DEEPL_API_KEY=\n")
                f.write("###\n")
        self.RVT_OPENAI_API_KEY = self.openai_entry.get()
        self.RVT_DEEPL_API_KEY = self.deepl_entry.get()
        openai.api_key = self.RVT_OPENAI_API_KEY
        with open('.env', 'w', encoding='utf-8') as file:
            file.write(f"RVT_OPENAI_API_KEY={self.RVT_OPENAI_API_KEY}\n")
            file.write(f"RVT_DEEPL_API_KEY={self.RVT_DEEPL_API_KEY}\n")
        print("設定を保存しました。")

    def save_audio_settings(self):
        self.selected_input_device = self.input_device_combobox.get()
        self.selected_output_device = self.output_device_combobox.get()
        with open('audio_settings.key', 'w', encoding='utf-8') as file:
            file.write(f"{self.selected_input_device}\n")
            file.write(f"{self.selected_output_device}\n")
        print("Audio settings saved.")

    def save_translate_language_lang(self):
        self.selected_language_lang = self.language_combobox_lang.get()
        print("Language setting saved:", self.selected_language_lang)

    def save_translate_language_input(self):
        self.selected_language_input = self.language_combobox_input.get()
        print("Language setting saved:", self.selected_language_input)

    def select_audio_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav *.mp3 *.flac")])
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)
    
    def start_file(self):
        file_path = self.file_entry.get()
        if self.selected_option.get() == 'file':
            self.process_audio_file(file_path)

    def toggle_enabled(self, state):
        self.is_enabled = state
        if self.is_enabled:
            self.on_button.configure(bg_color="green")
            self.off_button.configure(bg_color="gray")
            print("Enabled.")
        else:
            self.on_button.configure(bg_color="gray")
            self.off_button.configure(bg_color="red")
            print("Disabled.")
        print("Toggled:", self.is_enabled)

    def exit_app(self):
        self.is_enabled = False
        self.is_exit = True
        time.sleep(1)
        try:
            print('add: ', self.audio_dir)
            shutil.rmtree(self.audio_dir)
            print(f"Deleted audio folder: {self.audio_dir}")
        except Exception as e:
            print(f"Error deleting audio folder: {e}")
        print('app destroy')
        self.app.destroy()

    def open_settings(self):
        self.notebook.select(self.settings_frame)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def reset_program(self):
            self.is_enabled = False
            print("Resetting program")
            time.sleep(1)
            self.is_enabled = True

    def process_audio_file(self, audio_file_path):
        try:
            if self.selected_language == 'English to Japanese':
                language = 'en2ja'
                print(f"Processing audio file: {audio_file_path}")
                text = self.transcribe_audio_whisper(audio_file_path, language)
                if text is None:
                    print("No text found. Skipping processing.")
                    return
                language = 'ja'
                translated_text = self.translate_text_deepl(text, 'EN', 'JA')
                translated_text_str = translated_text.text if isinstance(translated_text, deepl.translator.TextResult) else translated_text
                print('translated_text: ', translated_text_str)
                self.text_to_speech_google(translated_text_str, language)

            elif self.selected_language == 'Japanese to English':
                language = 'ja2en'
                print(f"Processing audio file: {audio_file_path}")
                translated_text = self.transcribe_audio_whisper(audio_file_path, language)
                print('translated_text: ', translated_text)
                if translated_text is None:
                    print("No translated_text found. Skipping processing.")
                    return
                language = 'en'
                self.text_to_speech_google(translated_text, language)
        except Exception as e:
            print(f"paf-Error processing audio file: {e}")
            self.reset_program()

    def record_audio(self, outputDirWav):
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 48000
        CHUNK_DURATION_MS = 30
        PADDING_DURATION_MS = 300
        vad_strength = 1
        CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000) 
        NUM_PADDING_CHUNKS = int(PADDING_DURATION_MS / CHUNK_DURATION_MS)
        try:
            if not os.path.exists(outputDirWav):
                os.makedirs(outputDirWav)
            if self.selected_input_device:
                input_device_index = [device['name'] for device in sounddevice.query_devices()].index(self.selected_input_device)
                self.input_device_combobox.current(input_device_index)
            audio = pyaudio.PyAudio()
            stream = audio.open(format=FORMAT, channels=CHANNELS,
                                rate=RATE, input=True,
                                frames_per_buffer=CHUNK_SIZE,
                                input_device_index=input_device_index)
            print('input_device_index: ', input_device_index)
            vad = webrtcvad.Vad(vad_strength)
            with ThreadPoolExecutor(max_workers=5) as executor:
                frames = []
                silent_frames = 0
                frame_count = 0
                print('is_enabled2: ', self.is_enabled)
                while self.is_enabled:
                    chunk = stream.read(CHUNK_SIZE)
                    is_speech = vad.is_speech(chunk, RATE)
                    if not is_speech:
                        silent_frames += 1
                        if silent_frames > NUM_PADDING_CHUNKS and len(frames) > 0:
                            audio_length = len(frames) * CHUNK_SIZE / RATE
                            if audio_length >= 1.0:
                                frame_count += 1
                                path = "%s%d.wav" % (outputDirWav, frame_count)
                                with contextlib.closing(wave.open(path, 'wb')) as wf:
                                    wf.setnchannels(1)
                                    wf.setsampwidth(audio.get_sample_size(FORMAT))
                                    wf.setframerate(RATE)
                                    wf.writeframes(b''.join(frames))
                                executor.submit(self.process_audio_file, path)
                            frames = []
                            silent_frames = 0
                        time.sleep(0.1)
                    else:
                        silent_frames = 0
                        frames.append(chunk)
                    if not self.is_enabled:
                        print('break')
                        break
                stream.stop_stream()
                stream.close()
                audio.terminate()
                print('end')
        except Exception as e:
            print(f"ra-Error processing audio file: {e}")
            self.reset_program()

    def start_audio_processing(self):
        if self.selected_input_device is None or self.selected_output_device is None:
            print("Please setting in audio tab")
            return
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M")
        self.audio_dir = f"output/{timestamp}/"
        os.makedirs(self.audio_dir, exist_ok=True)
        while not self.is_exit:
            if self.is_enabled:
                self.record_audio(self.audio_dir)
            time.sleep(1)

    def transcribe_audio_whisper(self, audio_file_path, language):
        print(language)
        try:
            with open(audio_file_path, 'rb') as audio_file:
                if language == 'en2ja':
                    transcript = openai.Audio.transcribe('whisper-1', audio_file)
                    text = transcript['text']
                elif language == 'ja2en':
                    transcript = openai.Audio.translate('whisper-1', audio_file)
                    text = transcript['text']
            if not text.strip():
                return None
            return text
        except Exception as e:
            print(f"taw-Error processing audio file: {e}")
        self.reset_program()
    def translate_text_deepl(self, text, source_lang, target_lang):
        try:
            print('text2: ', text)
            if not text:
                print("No text to translate.")
            translator = deepl.Translator(self.RVT_DEEPL_API_KEY)
            result = translator.translate_text(text, source_lang=source_lang, target_lang=target_lang)
            print('result: ', result)
            return result
        except Exception as e:
            print(f"ttd-Error processing audio file: {e}")
            self.reset_program()

    def text_to_speech_google(self, text, language):
        print('speechText: ', text) 
        try:
            tts = gTTS(text=text, lang=language)
            temp_file = 'temp_file.mp3'
            tts.save(temp_file)
            audio_data, sample_rate = sf.read(temp_file)
            os.remove(temp_file)

            # 1.3倍速にリサンプリング
            new_length = int(audio_data.shape[0] / 1.3)
            resampled_audio_data = resample(audio_data, new_length)

            # dtypeをint16に変換
            resampled_audio_data = np.int16(resampled_audio_data * 32767)

            # 出力デバイスの設定
            if self.selected_output_device:
                output_device_index = [device['name'] for device in sounddevice.query_devices()].index(self.selected_output_device)
                self.output_device_combobox.current(output_device_index)
            with sounddevice.RawOutputStream(device=output_device_index, channels=1, samplerate=sample_rate, dtype='int16') as stream:
                time.sleep(0.2)
                stream.write(resampled_audio_data.tobytes())
        except Exception as e:
            print(f"ttsg-Error processing audio file: {e}")
            self.reset_program()

my_app = MyApplication()
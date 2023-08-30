## 🎙 リアルタイム音声翻訳機 🎙 

* これはリアルタイム音声翻訳アプリです🤖
* OpenAI APIとDeepLAPIを取得することで使用できます。
* また、VBCABLEという仮想オーディオデバイスをインストールし出力デバイスにすることで通話相手に処理後の声が届くようになります。


## 🔦インストール


* releasesから最新版のソースコードをインストールしてください。
* ``speech.exe``を実行し、settingタブにAPIキー、audioタブにデバイスを入力してください。


## 💡使い方


* 正しい音声デバイスが認識されると、マイクに喋りかけた声が翻訳され音声として出力されます。
* mainタブのON-OFFは、マイクが声を拾うかどうかのトリガーで、OFFの間は反応しなくなります。
* fileタブではファイルの音声を読み込むこともできます。


VBCABLEのインストール：[VBCABLE](https://vb-audio.com/Cable/)

## 注意等
* APIは.envに保存されます。
* Macを持っていないのでMacでは動作確認ができていません。
* サブPCで動作確認しましたが、もし不具合等ありましたらご連絡ください。

このアプリケーションは、他の方が開発した多くの素敵なライブラリを使用することで開発・公開することができました。
全ての関係者様に感謝しています。

## English

## 🎙 Real-time voice translator 🎙

* This is a real-time voice translation application 🤖
* You can use it by getting OpenAI API and DeepLAPI.
* You can also install a virtual audio device called VBCABLE and make it the output device so that the caller can hear your voice after processing.


## 🔦Installation


* Install the latest version of the source code from releases.
* Run ``speech.exe`` and enter your API key in the setting tab and your device in the audio tab.


## 💡How to use.


* When the correct audio device is recognized, the voice you speak into the microphone will be translated and output as voice.
* The main tab ON-OFF triggers whether the microphone picks up the voice or not, and it will not respond while it is OFF.
* The file tab can also be used to load audio from a file.


Installation of VBCABLE: [VBCABLE](https://vb-audio.com/Cable/)


## Notes, etc.
* API is stored in .env.
* We have not confirmed that it works on a Mac because we do not have a Mac.
* We have tested it on a sub PC, but if you find any problems, please let us know.

We were able to develop and publish this application by using many nice libraries developed by others.
We thank all parties involved.
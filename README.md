# 📚 Overview

## 🧑‍💻 Installation
1. Clone the repository:
    ```sh
    git clone https://github.com/AkshayKulkarni3467/RasaScribe.git
    ```
2. Navigate to the project directory:
    ```sh
    cd RasaScribe
    ```
3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## ✨ Quick Start
1. Get a gemini api key and set it as an environment variable with name 'GOOGLE_API_KEY' 
2. Get a youtube data v3 api key and set it as an environment variable with name 'YOUTUBE_API_KEY'
3. Replace `os.getenv['SQL_PW']` with your local database password in actions.py 
4. To set up a whatsapp testing sandbox, host your chatbot with ngrok and setup and account on twilio.
5. Get the sid, auth_token and whatsapp number and copy it to credentials.yml
6. In your cmd, type:
    ```sh
    rasa run actions
    ```
    ```sh
    python callback_server.py
    ```
    ```sh
    rasa run
    ```

## Contributing
1. Fork the repository.
2. Create a new branch: `git checkout -b feature-branch`
3. Make your changes and commit them: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-branch`
5. Open a pull request.

## Future Plans
- Adding audio suggestions for short form videos content.
- Adding a functionality of two stage fallback.
- Adding a functionality of posting image links and generating script based on that image.

## License
This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements
- Inspired by the hype of gen ai to come out and develop my own tools.
- Special thanks to the contributors and the open-source community.

## Contact
For more information, visit the [Project](https://github.com/AkshayKulkarni3467/RasaScribe).
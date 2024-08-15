# IChatBox
IChatBox is a user-friendly chat solution designed for easy integration into existing websites. It offers seamless real-time communication, is highly customizable, and enhances user engagement with minimal setup. Ideal for adding interactive features to any site.

# Run step:
## 1. Clone the repository
```bash
git clone https://github.com/yourusername/IChatBox.git
cd IChatBox
```
## 2. Set up a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate # On Windows, use `venv\Scripts\activate`
```
## 3. Install dependencies
```bash
pip install -r requirements.txt
```
## 4. Set up environment variables
Create a .env file in the root of your project, and define your environment-specific variables such as:

```bash
SECRET_KEY=your-secret-key
DEBUG=True
```
## 5. Apply migrations
```bash
python manage.py migrate
```
## 6. Create a superuser (optional but recommended for admin access)
```bash
python manage.py createsuperuser
```
## 7. Run the development server
```bash
python manage.py runserver
```
## 8. Access the chatbox
Open your browser and go to http://localhost:8000/ to see the IChatBox in action.

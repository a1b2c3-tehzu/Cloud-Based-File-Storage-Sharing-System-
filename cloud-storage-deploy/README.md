# Cloud-Based File Storage and Secure Sharing System

A web-based cloud file storage system built with Flask and AWS S3, featuring secure file sharing with expiry-based access control.

## 🚀 Features

- **User Authentication**: Secure registration and login system
- **File Upload**: Upload files to Amazon S3 cloud storage
- **File Management**: View, download, and delete files
- **Secure Sharing**: Generate shareable links with expiry dates
- **Access Control**: Token-based secure file access
- **Modern UI**: Bootstrap 5 responsive design

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Backend**: Python Flask
- **Cloud Storage**: Amazon S3
- **Database**: MySQL (XAMPP)
- **Authentication**: Session-based with password hashing

## 📋 Prerequisites

1. Python 3.7+
2. XAMPP (for MySQL)
3. AWS Account with S3 bucket
4. AWS IAM user credentials

## 🗄️ Database Setup

1. Start XAMPP and ensure MySQL is running
2. Execute the database schema:
   ```sql
   -- Run the database/schema.sql file in MySQL
   ```

## ⚙️ Configuration

1. **AWS Configuration**:
   - Create an S3 bucket in AWS
   - Create an IAM user with S3 permissions
   - Update `config.py` with your credentials:
     ```python
     AWS_ACCESS_KEY_ID = 'your_aws_access_key_here'
     AWS_SECRET_ACCESS_KEY = 'your_aws_secret_key_here'
     S3_BUCKET_NAME = 'your_s3_bucket_name_here'
     ```

2. **Database Configuration**:
   - Update `config.py` with your MySQL settings:
     ```python
     DB_HOST = 'localhost'
     DB_USER = 'root'
     DB_PASSWORD = ''  # Your MySQL password
     DB_NAME = 'cloud_storage_db'
     ```

## 🚀 Installation

1. **Clone/Download the project** to your desired directory

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

## 📁 Project Structure

```
cloud_storage_system/
├── app.py                    # Main Flask application
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── database/
│   └── schema.sql           # Database schema
├── models/
│   ├── db.py               # Database connection
│   ├── user_model.py       # User model
│   ├── file_model.py       # File model
│   └── share_model.py      # Share link model
├── routes/
│   ├── auth_routes.py      # Authentication routes
│   ├── file_routes.py      # File management routes
│   └── share_routes.py     # File sharing routes
├── utils/
│   └── s3_service.py       # AWS S3 service
├── static/
│   ├── css/style.css       # Custom styles
│   ├── js/main.js          # JavaScript functionality
│   └── temp_uploads/       # Temporary upload directory
└── templates/
    ├── base.html           # Base template
    ├── login.html          # Login page
    ├── register.html       # Registration page
    ├── dashboard.html      # User dashboard
    ├── upload.html         # File upload page
    ├── share.html          # File sharing page
    └── error.html          # Error page
```

## 🔐 Security Features

- Password hashing with Werkzeug
- Session-based authentication
- Token-based file sharing
- File type validation
- File size restrictions (16MB)
- SQL injection prevention
- CSRF protection ready

## 📝 Usage Guide

1. **Register**: Create a new account
2. **Login**: Access your dashboard
3. **Upload Files**: Store files in the cloud
4. **Manage Files**: View, download, or delete files
5. **Share Files**: Generate secure share links with expiry dates

## 🔧 API Routes

### Authentication Routes
- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - User logout

### File Routes
- `GET /dashboard` - User file dashboard
- `POST /upload` - Upload file to S3
- `GET /delete/<file_id>` - Delete file
- `GET /download/<file_id>` - Download file

### Share Routes
- `GET /generate-share/<file_id>` - Generate share link
- `GET /share/<token>` - Access shared file

## 🐛 Troubleshooting

**Database Connection Error**:
- Ensure XAMPP MySQL is running
- Check database credentials in config.py
- Verify database schema is imported

**AWS S3 Upload Error**:
- Verify AWS credentials are correct
- Check S3 bucket permissions
- Ensure bucket exists and is accessible

**File Upload Issues**:
- Check file size (max 16MB)
- Verify file type is allowed
- Ensure temp_uploads directory exists

## 📄 License

This project is for educational purposes. Use responsibly and ensure proper security measures in production.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📞 Support

For any queries or issues, please check the troubleshooting section or create an issue.

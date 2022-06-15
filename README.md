# aws uploader

Script that backup a folder to AWS.

Supports the following environment variables.
You can create an .env file in this repository to load it directly from disk.

### Environment
`ACCESS_KEY` and `SECRET_ACCESS_KEY` - Credentials from AWS needed to upload

`BUCKET` - Name of the bucket to upload into

`BACKUP_FOLDER` - Path to the folder we wish to backup

`UPLOAD_ROOT_FOLDER`[optional] - Prefix folder to the upload path

### Ignore file
You can add a `.ignore` file into the root of the repository. 
That file can contain `glob` paths that will be ignored when uploading.

__IMPORTANT__: These are glob paths and does _not_ follow the same pattern as the common .gitignore file.

```
.git/**      | Will match any thing under the git path
**/.DS_Store | Will match any file anywhere named exactly .DS_Store
```
import os
import datetime
import glob
class LogFileManager:
    """Manage log file operations: creation, organization, and retrieval"""

    def __init__(self, log_directory="keylogs"):
        self.log_directory = log_directory
        self._ensure_directory_exists()

    def _ensure_directory_exists(self):
        """Create log directory if it doesn't exist"""
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)

    def get_log_filename(self, date=None):
        """Generate log filename for a specific date (or today)"""
        if date is None:
            date = datetime.datetime.now()
        date_str = date.strftime("%Y-%m-%d")
        return os.path.join(self.log_directory, f"keylog_{date_str}.txt")

    def organize_files(self):
        """Organize log files by Month > Day > Year structure"""
        if not os.path.exists(self.log_directory):
            return {}

        log_files = glob.glob(os.path.join(self.log_directory, "keylog_*.txt"))
        organized = {}

        for filepath in log_files:
            filename = os.path.basename(filepath)
            try:
                date_part = filename.replace("keylog_", "").replace(".txt", "")
                date_obj = datetime.datetime.strptime(date_part, "%Y-%m-%d")

                month = date_obj.strftime("%B")
                day = date_obj.strftime("%d")
                year = date_obj.strftime("%Y")

                if month not in organized:
                    organized[month] = {}
                if day not in organized[month]:
                    organized[month][day] = []

                organized[month][day].append((year, filepath))
            except ValueError:
                continue

        return organized

    # def get_file_tail(self, filepath, num_lines=50):
    #     """Read las N lines of a file for better performance"""
    #     try:
    #         with open(filepath ,'r', encoding='utf-8') as f:
    #             lines = f.readline()
    #             return ''.join(lines[-num_lines:])
    #     except Exception as e:
    #         return ""

    def read_file(self, filepath):
        """Read content from a log file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Failed to read file: {str(e)}")

    def write_log(self, filepath, content):
        """Append content to a log file"""
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Error writing to log file: {e}")

    def delete_file(self, filepath):
        """Delete a log file"""
        try:
            os.remove(filepath)
            return True
        except Exception as e:
            raise IOError(f"Failed to delete file: {str(e)}")

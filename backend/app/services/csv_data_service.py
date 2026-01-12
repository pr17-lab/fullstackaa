import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class CSVDataLoader:
    """Service for loading and managing CSV data in memory."""
    
    def __init__(self):
        self.students_df: Optional[pd.DataFrame] = None
        self.records_df: Optional[pd.DataFrame] = None
        self._data_loaded = False
    
    def load_data(self):
        """Load CSV files into memory at application startup."""
        try:
            data_dir = Path(__file__).parent.parent.parent / "data"
            
            # Load student main info
            students_path = data_dir / "SATA_student_main_info_10k.csv"
            if students_path.exists():
                self.students_df = pd.read_csv(students_path)
                logger.info(f"Loaded {len(self.students_df)} student records")
            else:
                logger.warning(f"Student data file not found: {students_path}")
                self.students_df = pd.DataFrame()
            
            # Load academic records
            records_path = data_dir / "SATA_academic_records_10k.csv"
            if records_path.exists():
                self.records_df = pd.read_csv(records_path)
                logger.info(f"Loaded {len(self.records_df)} academic records")
            else:
                logger.warning(f"Academic records file not found: {records_path}")
                self.records_df = pd.DataFrame()
            
            self._data_loaded = True
            logger.info("CSV data loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading CSV data: {str(e)}")
            self.students_df = pd.DataFrame()
            self.records_df = pd.DataFrame()
            self._data_loaded = False
    
    def get_student_info(self, student_id: str) -> Optional[Dict]:
        """Get student information by ID."""
        if self.students_df is None or self.students_df.empty:
            return None
        
        student = self.students_df[self.students_df['student_id'] == student_id]
        if student.empty:
            return None
        
        return student.iloc[0].to_dict()
    
    def get_student_records(self, student_id: str) -> List[Dict]:
        """Get all academic records for a student."""
        if self.records_df is None or self.records_df.empty:
            return []
        
        records = self.records_df[self.records_df['student_id'] == student_id]
        return records.to_dict('records')
    
    def get_gpa_trend(self, student_id: str) -> List[Dict]:
        """Calculate GPA trend by semester for a student."""
        records = self.get_student_records(student_id)
        if not records:
            return []
        
        # Group by semester and calculate average marks
        df = pd.DataFrame(records)
        trend = df.groupby('semester').agg({
            'Total_marks': 'mean',
            'credits': 'sum'
        }).reset_index()
        
        # Convert marks to GPA scale (assuming 10-point scale)
        trend['gpa'] = (trend['Total_marks'] / 10).round(2)
        
        return trend[['semester', 'gpa', 'credits']].to_dict('records')
    
    def search_students(
        self, 
        department: Optional[str] = None,
        semester: Optional[int] = None,
        min_cgpa: Optional[float] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Search students with filters."""
        if self.students_df is None or self.students_df.empty:
            return []
        
        df = self.students_df.copy()
        
        # Apply filters
        if department:
            df = df[df['department'].str.contains(department, case=False, na=False)]
        if semester:
            df = df[df['current_semester'] == semester]
        if min_cgpa:
            df = df[df['cgpa'] >= min_cgpa]
        
        # Apply limit
        df = df.head(limit)
        
        return df.to_dict('records')
    
    @property
    def is_loaded(self) -> bool:
        """Check if data has been loaded."""
        return self._data_loaded

# Global instance
csv_data_loader = CSVDataLoader()

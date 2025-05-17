import random
import json
import logging
import os
from typing import List
from dataclasses import dataclass
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLAGS_JSON_PATH = os.path.join(PROJECT_ROOT, 'data', 'flags', 'flags.json')
FLAG_HTML_PATH = os.path.join(PROJECT_ROOT, 'data', 'flags', 'raw_flag_html.html')

class InvalidHtmlError(Exception):
    pass

class FlagLoadError(Exception):
    pass

@dataclass
class Flag:
    name: str
    by: str

class FlagHandler:
    def __init__(self):
        """
        Initialize the FlagHandler with a list of flag images.
        """
        self._load_flags_from_file()

    @property
    def flags(self) -> List[Flag]:
        """Get the current list of flag images."""
        return self._flags.copy()  # Return a copy to prevent direct modification
    
    def get_random_flag(self) -> Flag:
        """
        Return a random flag from the list.
        
        Returns:
            Dict in format { flag_url, flag_creator)
        """
        if not self._flags:
            raise ValueError("No flag images available")

        flag = random.choice(self._flags)
        logger.info(f"Selected flag: {flag}")

        return flag
    
    def generate_flag_url(self, flag) -> str:
        """Generate a flag url for the supplied flag based on name."""
        SA_URL = 'https://fi.somethingawful.com/images/impzone/flags/'
        url = SA_URL + flag.name
        return url

    def get_random_flag_url(self, with_creator_metadata=False) -> str:
        """
        Get a random flag's redirect URL.

        Args:
            with_creator_metadata (Boolean, optional): 
                whether to append creator name to url as query parameter
        
        Returns:
            URL of a random flag.
        """
        flag = self.get_random_flag()
        url = self.generate_flag_url(flag)

        if with_creator_metadata:
            url += f'?by={flag.by}'
        
        return url

    def get_random_flag_url_with_metadata(self) -> str:
        """
        Get a redirect URL with creator as query parameter.
            
        Returns:
            URL of a random flag with creator as query parameter.
        """
        flag = self.get_random_flag()
        url = self.generate_flag_url(flag)

        return url + f'?by={flag.by}'
    
    def get_flag_list_from_html(self) -> List[Flag]:
        """
        Generate a list of Flag objects from table html.
        
        Returns:
            List of Flag objects
        """
        flag_cells = self._load_drive_table_cells()
        parsed_flags = []

        for cell in flag_cells:
            parsed_flags.append(self._parse_flag_cell_data(cell))

        logger.info(f'Parsed {len(parsed_flags)} flags successfully.')
        sorted_flags = self.sort_flags_by_name(parsed_flags)
        return sorted_flags
    
    def add_flags_to_file(self, new_flags) -> None:
        """
        Adds supplied list of flags to instance flag list and saves to file.

        Args: 
            new_flags (List[Flag]): List of flags to add to existing list
        """
        combined_flags = self.flags + new_flags
        sorted_flags = self.sort_flags_by_name(combined_flags)
        self._flags = sorted_flags

        logger.info(f'Saving combined list of {len(self._flags)} to file.')
        self._save_to_file()
        logger.info('Successfully updated flag list file!')

    def sort_flags_by_name(self, flags: List[Flag]) -> List[Flag]:
        """
        Sort a list of Flag objects alphabetically by their name attribute.
        
        Args:
            flags (List[Flag]): List of Flag objects to sort
            
        Returns:
            List[Flag]: Sorted list of Flag objects
        """
        return sorted(flags, key=lambda flag: flag.name.lower())

    def _load_flags_from_file(self) -> None:
        """
        Load image URLs from the JSON file.
        """
        try:
            with open(FLAGS_JSON_PATH, 'r') as file:
                data = json.load(file)
                self._flags = [Flag(**flag_data) for flag_data in data.get('flags', [])]
        except FileNotFoundError:
            message = f"{FLAGS_JSON_PATH} file not found"
            logger.error(message)
            raise FlagLoadError(message)
        except json.JSONDecodeError:
            message = f"Invalid JSON in {FLAGS_JSON_PATH}"
            logger.error(message)
            raise FlagLoadError(message)
        except Exception as e:
            message = f"Error loading flags from file: {str(e)}"
            logger.error(message)
            raise FlagLoadError(message)
        
    def _load_drive_table_cells(self, source_html_path=FLAG_HTML_PATH) -> List:
        """
        Get file name data from a Google Drive table.

        Returns:
            List of BeautifulSoup objects collected from the raw html of a Google Drive table.

        Intended for use with raw html collected from a Google Drive page. Brittle; may stop working if
        the shape of the html in these tables changes, as it's predicated on class name.
        """
        # Current class name for Google Drive file name cells; change if necessary
        FLAG_NAME_CELL_CLASS = 'tyTrke M3pype'
        try:
            with open(source_html_path, 'r', encoding="utf-8") as file:
                html = file.read()
                soup = BeautifulSoup(html, features="html.parser")
        except Exception as e:
            logger.error(f"Error reading html file: {str(e)}")
            raise

        flag_cells = soup.find_all('div', FLAG_NAME_CELL_CLASS)
        row_count = len(flag_cells)
        if row_count == 0:
            message = f"No cell data loaded from table html at {source_html_path}. \
                Check that your html is valid and the cell class hasn't changed."
            raise InvalidHtmlError(message)
        
        logger.info(f'Loaded {len(flag_cells)} cells of flag names from {source_html_path}')
        return flag_cells

    def _parse_flag_cell_data(self, cell) -> Flag:
        """
        Retrieve the flag name and created-by from html table data.

        Args:
            cell: BeautifulSoup flag cell object retrieved from Google Drive table
        
        Returns:
            Flag object
        """
        flag_name = cell.text
        # standardized flag names follow format 'name - creator.png'
        name_components = flag_name.split(' - ')
        if len(name_components) == 2:
            # flag name fits expectation. strip off file extension to get creator
            smaller_name_chunks = name_components[1].split('.')
            # remove the last section (file extension) and rejoin since some users have periods in their names
            creator = '.'.join(smaller_name_chunks)
            # special cases
            if creator == 'TLD':
                creator = 'That Little Demon'
            elif creator == 'SC64':
                creator = 'Stone Cold 64'
            elif creator == 'pleb':
                creator = 'Plebian Parasite'
        else:
            logger.warn(f'Flag {flag_name} name is malformed; please manually add creator.')
            creator = ''
        
        return Flag(name=flag_name, by=creator)

    def _save_to_file(self) -> None:
        """Save the current list of flag images to the JSON file."""
        try:
            with open(FLAGS_JSON_PATH, 'w') as file:
                json.dump({
                    'flags': [
                        {'name': flag.name, 'by': flag.by}
                        for flag in self._flags
                    ]
                }, file, indent=4)
        except Exception as e:
            logger.error(f"Error saving flag images to file: {str(e)}")
            raise

import sys
import re

class FlashCode(object):
  """Handles interactive tutorial/module through hooks passed from a Watchman and
  from input/output validation. Requires a log_filename (updated by a Watchman) for
  validation. Validates through a Teacher."""

  def __init__(self, log_fname, teacher):
    super(FlashCode, self).__init__()

    # Logging
    self.logname = log_fname
    self.reset_io()

    # Teacher/Question
    self.teacher = teacher
    self.current = self.teacher.next()

    # Hook validation
    self.changed = False
    self.empty_prompt = re.compile(r".+\(\d+\).+(>>>|\.\.\.)\s*$")
    self.full_prompt  = re.compile(r""" .+(\(\d+\))           # group 1, matches '(#)'
                                        .+(>>>|\.\.\.)\s(.+)  # group 2, matches input
                                    """, re.X)
  
  def reset_io(self):
    self.input = []
    self.output = []
  
  ###
  # Core Methods
  ###
  def sprint(self, data):
    """Safe print. Prints directly to sys.__stdout__, bypassing Watchman logging."""

    string = "\n\n{0}(FC){1} {2}\n".format('\033[96m', '\033[0m', str(data))
    sys.__stdout__.write(string)
  
  def after_write(self):
    """Primary hook. Called after a write to stdout/err."""

    # Update object's list of input and output
    self._parse_log()
    
    # Validate hook call through input/output
    if (self.changed and self.current) and self._validated():

      # Set current question
      self.current = self.teacher.next()

      # Print next task, or if module is complete, inform user
      if self.current:
        self.sprint('\n'.join(self.current.task))
      else:
        self.sprint("Congrats! You've finished this module.\nPress CTRL-d to choose another when you're ready.") 
  
  ###
  # Private Methods
  ###
  def _validated(self):
    """Primary validation through current question's i/o regex patterns."""

    # Assume both are true, as both input and output may not be tested
    validi = True
    valido = True

    # Only test input and output if declared in current question (self.current.test)
    if 'i' in self.current.test and self.input:
      validi = True if self.current.i.match(self.input[-1]) else False
    if 'o' in self.current.test and self.output:
      valido = True if self.current.o.match(self.output[-1]) else False
    
    # The hook call is only valid if both input and output are valid
    return validi and valido
  
  def _parse_log(self):
    """Parse and read in log. Store input and output in attributes. Set self.changed
    if output has changed by updating."""

    # Store old output and reset
    oldout = list(self.output)
    self.reset_io()
    
    with open(self.logname, 'r') as log:

      for i, line in enumerate(log.readlines()):
        line = line.strip()

        # Full_prompt indicates user input. The log will be updated on
        # a fresh prompt as well, so we have to check for it.
        fullmatch = self.full_prompt.match(line)
        emptymatch = self.empty_prompt.match(line)

        # Skip banner and initial task prompt (both are logged)
        if 0 <= i <= (4 + len(self.teacher.q(0).task)):
          pass
        
        # Only store if user input is present
        elif fullmatch:
          self.input.append(fullmatch.group(3))
        
        elif emptymatch:
          pass
        
        # If there's no prompt match, it must be output
        else:
          self.output.append(line)
    
    # Validate change
    self.changed = True if self.output != oldout else False

  # Bugged and shitty. Currently unused.
  def _last_input_block(self):
    """Returns the last block of input submitted. An interpreter code block
    begins with a '>>>' prompt followed by 0 or more '...' prompts."""
    prompt = re.compile(r"\(\d+\)(>>>|...)\s.+")
    block = []

    if self.input:
      xinput = list(self.input)
      for i in range(len(xinput)-1, -1, -1):
        match = prompt.match(xinput[i])
        if match:
          if match.group(1) == '>>>':
            block.insert(0, xinput[i])
            return block
          elif match.group(1) == '...':
            block.insert(0, xinput.pop(i))
    return block

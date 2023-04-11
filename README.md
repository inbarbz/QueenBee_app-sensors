
### The main filter code file is on 
<code>
streamlit_app.py
 </code>

### Thesensors code include:
<code>
  UV_sensor_function_test.ino
  db_test1.ino
  </code>


### To install
<code>
pip install -r requirements.txt
</code>
<br/>

### Update config.toml to refresh video files
This file often store in path: “C:\Users\user\.streamlit\config.toml”.
Open the file “config.toml”, and add the following text in it:

<code>
!> cd <br/>
!> pwd <br/>
!> mkdir .streamlit <br/>
!> cd .streamlit <br/>
!> nano config.toml <br/>
</code>

add the following lines and then press Ctrl+x to exit and save <br/>
the file:

<code>
[server] <br/>
runOnSave = true
</code>

### To run our filter please enter the following in yout VisualSudio terminal:
<code>
streamlit run streamlit_app.py 
</code>


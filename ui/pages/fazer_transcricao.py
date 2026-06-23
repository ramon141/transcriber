import streamlit as st

from ui.state import init_state

init_state()

step: int = int(st.session_state.get("wizard_step", 1))

if step == 1:
    from ui.wizard.step1_upload import render
    render()
elif step == 2:
    from ui.wizard.step2_config import render
    render()
elif step == 3:
    from ui.wizard.step3_corte import render
    render()
elif step == 4:
    from ui.wizard.step4_processar import render
    render()
elif step == 5:
    from ui.wizard.step5_notion import render
    render()
else:
    st.session_state.wizard_step = 1
    st.rerun()

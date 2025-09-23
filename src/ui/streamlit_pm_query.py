# src/ui/streamlit_pm_query.py
import streamlit as st
import requests
import json
from typing import Any, Dict, List

BACKEND_URL = st.secrets.get('backend_url', 'http://127.0.0.1:8001')


def query_backend(query_text: str) -> Dict[str, Any]:
    url = f"{BACKEND_URL}/query"
    resp = requests.post(url, json={"query": query_text}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def select_backend(state: Dict[str, Any], selected_index: int) -> Dict[str, Any]:
    url = f"{BACKEND_URL}/query/select"
    resp = requests.post(url, json={"state": state, "selected_index": selected_index}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _append_message(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})


def _safe_rerun():
    """Call Streamlit's experimental rerun if available, otherwise do nothing.

    Some Streamlit versions/environments don't expose experimental_rerun. This helper
    avoids AttributeError during import/run in those environments.
    """
    try:
        rerun = getattr(st, 'experimental_rerun', None)
        if callable(rerun):
            rerun()
    except Exception:
        # Last-resort no-op
        return


def _show_raw_data(raw: Any):
    if raw is None:
        return
    with st.expander("Show raw data"):
        st.json(raw)


def main():
    st.set_page_config(page_title="Air Quality Chat", layout="wide")
    st.title("🌍 Air Quality Chat — Ask about PM2.5")

    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'workflow_state' not in st.session_state:
        st.session_state.workflow_state = None
    if 'waiting_for_selection' not in st.session_state:
        st.session_state.waiting_for_selection = False
    if 'last_error' not in st.session_state:
        st.session_state.last_error = None
    if 'pending_retry' not in st.session_state:
        st.session_state.pending_retry = None

    # Chat column layout
    chat_col, side_col = st.columns([3, 1])

    with chat_col:
        # Display chat history as chat messages
        for message in st.session_state.messages:
            role = message.get('role', 'assistant')
            content = message.get('content', '')
            # Use Streamlit chat components when available
            try:
                with st.chat_message(role):
                    st.write(content)
            except Exception:
                st.write(f"{role}: {content}")

        # If waiting for disambiguation, show options above the input
        if st.session_state.waiting_for_selection and st.session_state.workflow_state:
            st.info("Which location did you mean? Click one of the options below.")
            locations = st.session_state.workflow_state.get('locations', []) or []

            for idx, loc in enumerate(locations):
                label = loc.get('display_name') or loc.get('name') or f"Option {idx}"
                cols = st.columns([0.1, 0.8, 0.1])
                with cols[1]:
                    if st.button(label, key=f"select_loc_{idx}"):
                        # perform selection
                        with st.spinner('Fetching PM2.5 data...'):
                            try:
                                result = select_backend(st.session_state.workflow_state, idx)
                                data = result.get('data', {})
                                formatted = data.get('formatted_response')
                                raw = data.get('raw_data')

                                _append_message('assistant', formatted or str(raw))
                                _show_raw_data(raw)

                                st.session_state.waiting_for_selection = False
                                st.session_state.workflow_state = None
                                st.session_state.last_error = None
                                _safe_rerun()
                            except requests.exceptions.HTTPError as e:
                                # Backend returned a non-2xx response
                                try:
                                    detail = e.response.json()
                                except Exception:
                                    detail = e.response.text if getattr(e, 'response', None) is not None else str(e)
                                st.session_state.last_error = {
                                    'type': 'select',
                                    'message': f"Backend error ({getattr(e.response, 'status_code', '')}): {detail}",
                                    'state': st.session_state.workflow_state,
                                    'selected_index': idx,
                                }
                                _append_message('assistant', f"Error contacting backend: {detail}")
                                _safe_rerun()
                            except requests.RequestException as e:
                                # Network/other request-level error
                                st.session_state.last_error = {
                                    'type': 'select',
                                    'message': str(e),
                                    'state': st.session_state.workflow_state,
                                    'selected_index': idx,
                                }
                                _append_message('assistant', f"Error contacting backend: {e}")
                                _safe_rerun()

        # Chat input box
        user_text = st.chat_input("Ask me: e.g. 'what is the PM2.5 at Ambedkar Nagar'...")
        if user_text:
            _append_message('user', user_text)
            # call backend
            with st.spinner('Searching...'):
                try:
                    result = query_backend(user_text)
                except requests.RequestException as e:
                    # Save last error and allow user to retry
                    st.session_state.last_error = {
                        'type': 'query',
                        'message': str(e),
                        'user_text': user_text,
                    }
                    _append_message('assistant', f"Failed to contact backend: {e}")
                    _safe_rerun()
            print("inside streamlit_pm_query.py")
            print(user_text)
            data = result.get('data', {}) or {}
            state = result.get('state')
            print("state is : ",state)
            if state and state.get('waiting_for_user'):
                st.session_state.workflow_state = state
                st.session_state.waiting_for_selection = True
                _append_message('assistant', 'I found multiple matches for that location. Please select one below.')
                # show the locations immediately
                _safe_rerun()
            else:
                formatted = data.get('formatted_response')
                raw = data.get('raw_data')
                _append_message('assistant', formatted or str(raw))
                _show_raw_data(raw)
                _safe_rerun()

    with side_col:
        st.header('Tips')
        st.write('- Ask: "what is the current PM2.5 in <location>"')
        st.write('- If multiple locations are found you will be asked to select one')
        st.write('- Backend URL is read from `.streamlit/secrets.toml` key `backend_url`')

        # Show last error and allow retry
        if st.session_state.last_error:
            err = st.session_state.last_error
            st.error(err.get('message'))
            if st.button('Retry', key='retry_last'):
                st.session_state.pending_retry = err
                _safe_rerun()

    # Process pending retry actions (after layout) — perform the saved action
    if st.session_state.pending_retry:
        pending = st.session_state.pending_retry
        st.session_state.pending_retry = None
        if pending.get('type') == 'query':
            # Retry last query
            user_text = pending.get('user_text')
            if user_text:
                _append_message('user', user_text)
                try:
                    result = query_backend(user_text)
                except requests.RequestException as e:
                    st.session_state.last_error = {'type': 'query', 'message': str(e), 'user_text': user_text}
                    _append_message('assistant', f"Retry failed: {e}")
                else:
                    data = result.get('data', {}) or {}
                    state = result.get('state')
                    if state and state.get('waiting_for_user'):
                        st.session_state.workflow_state = state
                        st.session_state.waiting_for_selection = True
                        _append_message('assistant', 'I found multiple matches for that location. Please select one below.')
                    else:
                        formatted = data.get('formatted_response')
                        raw = data.get('raw_data')
                        _append_message('assistant', formatted or str(raw))
                        _show_raw_data(raw)

        elif pending.get('type') == 'select':
            state = pending.get('state')
            idx = pending.get('selected_index')
            if state is not None and idx is not None:
                try:
                    result = select_backend(state, idx)
                except requests.RequestException as e:
                    st.session_state.last_error = {'type': 'select', 'message': str(e), 'state': state, 'selected_index': idx}
                    _append_message('assistant', f"Retry failed: {e}")
                else:
                    data = result.get('data', {})
                    formatted = data.get('formatted_response')
                    raw = data.get('raw_data')
                    _append_message('assistant', formatted or str(raw))
                    _show_raw_data(raw)


if __name__ == '__main__':
    main()
import streamlit as st
import pymongo
import streamlit_authenticator as stauth
import datetime

st.set_page_config(page_title="ChatGPT Prompt Hub", page_icon="🔮", layout="wide", initial_sidebar_state="auto", menu_items=None)

# Initialize connection. Uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    client = pymongo.MongoClient(f"mongodb+srv://admin:{st.secrets['mongo']['db_password']}@cluster0.rkiigil.mongodb.net/?retryWrites=true&w=majority")
    db = client.PromptHub
    return db
db = init_connection()

def get_prompt_items(force = False):
    if force or "all_prompt_ids" not in st.session_state:
        prompts = db.Prompts.find()
        prompt_items = list(prompts)  # make hashable for st.experimental_memo
        st.session_state["all_prompt_ids"] = [prompt["_id"] for prompt in prompt_items]
        st.session_state["prompt_dict"] = {prompt["_id"]: prompt for prompt in prompt_items}

def get_user_items(force = False):
    if force or "users_dict" not in st.session_state:
        users = db.Users.find()
        user_items = list(users)
        st.session_state['users_dict'] = {user["_id"]: user for user in user_items}
        st.session_state['usernames'] = {user["username"] for user in user_items}
        st.session_state['id_username_dict'] = {user["_id"]: user["username"] for user in user_items}
        st.session_state['username_id_dict'] = {user["username"]: user["_id"] for user in user_items}
        st.session_state['password_dict'] = {"usernames": {user["username"]: {"name": user["username"], "password": user["password"]} for user in user_items}}

page = st.sidebar.selectbox("Page", ["Explore", "My Collections", "Create"])
title_column, login_column = st.columns([6,1])
title_column.markdown("## :crystal_ball: ChatGPT Prompt Hub")


def render_prompts(prompt_ids, n_column = 3):
    # prompts = st.session_state["prompts"]
    grouped_prompt_ids = [prompt_ids[n_column*k:n_column*k+n_column] for k in range(len(prompt_ids)//n_column + 1)]
    for n_prompt_ids in grouped_prompt_ids:
        n_prompts = [st.session_state["prompt_dict"][prompt_id] for prompt_id in n_prompt_ids]
        st_2n_columns = st.columns(n_column * [2,1])
        for column_i, item in enumerate(n_prompts):
            st_2n_columns[2*column_i].markdown(f"""##### {item['title']}""")
            author = item['authorName']
            if author == "":
                author = "Anonymous"
                if 'id_username_dict' in st.session_state:
                    author = st.session_state['id_username_dict'][item['author']]
            st_2n_columns[2*column_i+1].markdown(f"*By {author}*")
        st_n_columns = st.columns(n_column)
        for column_i, item in enumerate(n_prompts):
            st_n_columns[column_i].info(item['content'])


        # favorite button
        st_2n_columns = st.columns(n_column * [2,1])
        for column_i, item in enumerate(n_prompts):
            favor_col = st_2n_columns[2*column_i].empty()
            if "username" in st.session_state and st.session_state["username"] != "":
                is_favor = item["_id"] in st.session_state['users_dict'][st.session_state['username_id_dict'][st.session_state["username"]]]["favorPrompts"]
            else:
                is_favor = False

            change_favor = favor_col.button(f"{':heart:' if is_favor else '🤍'} {item['numFavor']}", key = "heart" + item['content']) # 
            if change_favor:
                if "username" in st.session_state and st.session_state["username"] != "":
                    is_favor = not is_favor
                    if is_favor:
                        db.Users.update_one({"username": st.session_state["username"]}, {"$push": {"favorPrompts": item["_id"]}})
                        db.Prompts.update_one({"_id": item["_id"]}, {"$inc": {"numFavor": 1}})
                        item['numFavor'] += 1
                        st.session_state['users_dict'][st.session_state['username_id_dict'][st.session_state["username"]]]["favorPrompts"].append(item["_id"])
                    else:
                        db.Users.update_one({"username": st.session_state["username"]}, {"$pull": {"favorPrompts": item["_id"]}})
                        db.Prompts.update_one({"_id": item["_id"]}, {"$inc": {"numFavor": -1}})
                        item['numFavor'] -= 1
                        st.session_state['users_dict'][st.session_state['username_id_dict'][st.session_state["username"]]]["favorPrompts"].remove(item["_id"])
                    change_favor = favor_col.button(f"{':heart:' if is_favor else '🤍'} {item['numFavor']}", key = "changedheart" + item['content'])
                else:
                    st.error("Please log in to favorite a prompt.")
            
            flag_col = st_2n_columns[2*column_i + 1].empty()
            if "username" in st.session_state and st.session_state["username"] != "":
                is_flag = item["_id"] in st.session_state['users_dict'][st.session_state['username_id_dict'][st.session_state["username"]]]["flagPrompts"]
            else:
                is_flag = False

            change_flag = flag_col.button(f"{'⚠️' if is_flag else '❕'} {item['numFlag']}", key = "flag" + item['content']) # 
            if change_flag:
                if "username" in st.session_state and st.session_state["username"] != "":
                    is_flag = not is_flag
                    if is_flag:
                        db.Users.update_one({"username": st.session_state["username"]}, {"$push": {"flagPrompts": item["_id"]}})
                        db.Prompts.update_one({"_id": item["_id"]}, {"$inc": {"numFlag": 1}})
                        item['numFlag'] += 1
                        st.session_state['users_dict'][st.session_state['username_id_dict'][st.session_state["username"]]]["flagPrompts"].append(item["_id"])
                    else:
                        db.Users.update_one({"username": st.session_state["username"]}, {"$pull": {"flagPrompts": item["_id"]}})
                        db.Prompts.update_one({"_id": item["_id"]}, {"$inc": {"numFlag": -1}})
                        item['numFlag'] -= 1
                        st.session_state['users_dict'][st.session_state['username_id_dict'][st.session_state["username"]]]["flagPrompts"].remove(item["_id"])
                    change_flag = flag_col.button(f"{'⚠️' if is_flag else '❕'} {item['numFlag']}", key = "changedflag" + item['content'])
                else:
                    st.error("Please log in to flag a prompt.")

            # flag button
            # flag_col = st_2n_columns[2*column_i + 1].empty()
            # if "username" in st.session_state and st.session_state["username"] != "":
            #     is_flag = item["_id"] in st.session_state['users_dict'][st.session_state['username_id_dict'][st.session_state["username"]]]["flagPrompts"]
            # else:
            #     is_flag = False
            # change_flag = flag_col.button(f"{'⚠️' if is_flag else '❕'} {item['numFlag']}", key = "flag" + item['content']) # 
            # if change_flag:
            #     if "username" in st.session_state and st.session_state["username"] != "":
            #         is_flag = not is_flag
            #         if is_flag:
            #             db.Users.update_one({"username": st.session_state["username"]}, {"$push": {"flagPrompts": item["_id"]}})
            #             db.Prompts.update_one({"prompts": item["_id"]}, {"$inc": {"numFlag": 1}})
            #             item['numFlag'] += 1
            #         else:
            #             db.Users.update_one({"username": st.session_state["username"]}, {"$pull": {"flagPrompts": item["_id"]}})
            #             db.Prompts.update_one({"prompts": item["_id"]}, {"$inc": {"numFlag": -1}})
            #             item['numFlag'] -= 1
            #         change_flag = flag_col.button(f"{'⚠️' if is_flag else '❕'} {item['numFlag']}", key = "changedflag" + item['content'])
                    
            #     else:
            #         st.error("Please log in to flag a prompt.")
        
if page == "Explore":
    st.write("### Explore Prompts")
    st.session_state["all_prompt_ids"] = []
    get_prompt_items()
    get_user_items()
    render_prompts(st.session_state["all_prompt_ids"])


if page == "My Collections":
    st.write("### :heart: My Favorite Prompts")
    prompt_dict = st.session_state["prompt_dict"]
    if "username" in st.session_state and st.session_state["username"] != "":
        get_user_items(force=True)
        favor_prompt_ids = st.session_state["users_dict"][st.session_state['username_id_dict'][st.session_state["username"]]]["favorPrompts"]
        render_prompts(favor_prompt_ids)
    else:
        st.error("Please log in to view your favorite prompts.")


if page == "Create":
    st.write("### Create A Prompt :writing_hand:")
    with st.form("write_prompt"):
        title = st.text_input("Title")
        prompt = st.text_area("Prompt")
        language = st.selectbox("Language", ["English", "Chinese", "Arabic", "French", "Russian", "Spanish"])
        if "username" in st.session_state and st.session_state["username"] != "":
            author = ""
            author_id = st.session_state['username_id_dict'][st.session_state["username"]]
        else:
            author = st.text_input("Username")
        submitted = st.form_submit_button("Submit")
        if submitted:
            if title == "":
                st.error("Please enter a title.")
            elif prompt == "":
                st.error("Please enter a prompt.")
            else:
                st.success("Thank you for submitting!")
                result = db.Prompts.insert_one({"title": title, "content": prompt, "language": language, "author": author_id, "authorName": author, "createdAt": datetime.datetime.now(), "numFavor": 0, "numFlag": 0})
                get_prompt_items(force = True)

get_user_items()
authenticator = stauth.Authenticate(
    credentials = st.session_state['password_dict'],
    cookie_name = "random_cookie_name",
    key = "random_signature_key",
    cookie_expiry_days = 30,
    preauthorized = []
)
if "username" not in st.session_state or st.session_state["username"] == "" or "authentication_status" not in st.session_state or st.session_state["authentication_status"] != True:
    login_reg = st.sidebar.radio("login", ["Login", "Register"], label_visibility = "hidden")
    if login_reg == "Login":
        
        name, authentication_status, username = authenticator.login('', 'sidebar')
        if st.session_state["authentication_status"] == False:
            st.sidebar.error('Username/password is incorrect')
        elif st.session_state["authentication_status"] == None:
            st.sidebar.warning('Please enter your username and password')
    elif login_reg == "Register":
        with st.sidebar.form("register"):
            username = st.text_input("Username")
            password = st.text_input("Password", type = "password")
            submitted = st.form_submit_button("Submit")
            if submitted:
                if username == "":
                    st.error("Please enter a username.")
                elif username in st.session_state['usernames']:
                    st.error("Username already exists.")
                elif password == "":
                    st.error("Please enter a password.")
                else:
                    st.success("Thank you for registering!")
                    hashed_password = stauth.Hasher([password]).generate()[0]
                    result = db.Users.insert_one({"username": username, "password": hashed_password, "favorPrompts": [], "createdAt": datetime.datetime.now()})
                    get_user_items(force = True)
else:
    st.sidebar.write(f'#### Welcome **{st.session_state["name"]}**')
    authenticator.logout('Logout', 'sidebar')

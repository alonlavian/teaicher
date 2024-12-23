-- Create users table
create table users (
    id uuid primary key default uuid_generate_v4(),
    email text unique not null,
    username text unique not null,
    password_hash text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    last_login timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create learning_sessions table
create table learning_sessions (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid references users(id) not null,
    subject text not null,
    problems_attempted integer default 0,
    problems_solved integer default 0,
    hints_used integer default 0,
    score integer default 0,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    started_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create RLS policies
alter table users enable row level security;
alter table learning_sessions enable row level security;

-- Users can only read their own data
create policy "Users can view own data" on users
    for select using (auth.uid() = id);

-- Users can update their own data
create policy "Users can update own data" on users
    for update using (auth.uid() = id);

-- Users can view their own learning sessions
create policy "Users can view own learning sessions" on learning_sessions
    for select using (auth.uid()::text = user_id::text);

-- Users can create their own learning sessions
create policy "Users can create own learning sessions" on learning_sessions
    for insert with check (auth.uid()::text = user_id::text);

-- Users can update their own learning sessions
create policy "Users can update own learning sessions" on learning_sessions
    for update using (auth.uid()::text = user_id::text);

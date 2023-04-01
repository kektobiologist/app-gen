lines = []

while True:
    user_input = input()

    # 👇️ if user pressed Enter without a value, break out of loop
    if user_input == '':
        break
    else:
        lines.append(user_input + '\n')


# 👇️ prints list of strings
print(lines)

# 👇️ join list into a string
print(''.join(lines).strip())
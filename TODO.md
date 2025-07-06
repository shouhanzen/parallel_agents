Hello! This is the TODO list for the verifier project. If you are an agent, feel free to mark items as "taken" and "completed" as you go. If you are looking to pickup a task, take the first one that is not marked as "taken" and "completed". Thanks.
If you're Claude code, don't turn the entire list into a todo list for you to consume. Just create 2 todo items. 1. you need to claim the task. 2. you need to complete the task. Also don't wait for user confirmation to start working on the task. Just start working on the task.

✅ create cli commands for listing active parallel agents - COMPLETED
✅ create cli commands for streaming out logs of those agents (make it work) - COMPLETED  
✅ create cli commands for listing changes in working sets - COMPLETED
✅ create cli commands for elevating changes from working sets - COMPLETED
✅ create parallel agent that reviews src and suggests potential changes into potential_todo.jsonl - COMPLETED
✅ make it so elevating changes from potential_todo.jsonl is possible. it just gets a claude code instance to actually make the changes directly over source code. - COMPLETED

✅ okay now write a bunch of e2e tests to make sure that the verifier system is actually detecting file changes and running/updateing claude code instances to write tests and docs and stuff. - COMPLETED
encourage the parallel agents to copy existing tests/docs/etc as a starting point before writing out new tests and making changes to docs.
also encourage the parallel agents to flag whichever changes they made with comments "this is the change! --- kidna idea basically"
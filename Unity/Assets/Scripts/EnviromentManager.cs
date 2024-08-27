using System.Collections;
using System.Collections.Generic;
using System.Runtime.ExceptionServices;
using UnityEngine;

public class EnviromentManager : MonoBehaviour
{
    // Set this with a slider to set the delay in which in iteration is finished and we send the current enviroment info to the server
    [Header("Manager parameters")]
    [SerializeField] private float delay = 10f;
    public static float iterationDelay;

    private List<int> agentIds = new List<int>();

    public delegate void AgentActionDelegate(int Id, string action);
    public static event AgentActionDelegate OnAgentAction;
    private char[] directions = Agent.directionNames;

    private void Awake()
    {
        iterationDelay = delay;
    }

    public void Initialize(int agents)
    {
        for (int i = 0; i < agents; i++)
        {
            agentIds.Add(i);
        }

        StartCoroutine(RandomMovementCoroutine());
    }

    private IEnumerator RandomMovementCoroutine()
    {
        while (true)
        {
            yield return new WaitForSeconds(iterationDelay);

            foreach (int agentId in agentIds)
            {
                char randomDirection = directions[Random.Range(0, directions.Length)];
                string instruction = $"M{randomDirection}";
                OnAgentAction?.Invoke(agentId, instruction);
            }
        }
    }

}
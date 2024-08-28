using System.Collections.Generic;
using System.Threading.Tasks;
using Unity.VisualScripting;
using UnityEngine;

public class Agent : MonoBehaviour
{
    private TaskCompletionSource<bool> actionCompletionSource;

    [Header("Agent values")]
    public int id;
    public Vector2Int pos;
    public Dictionary<char, int> cols = new Dictionary<char, int>
    {
    {'F', 0},
    {'B', 0},
    {'L', 0},
    {'R', 0}
    };

    public bool hasObject = false;
    public bool hasCollided = false;

    private Object grabbedObject;

    [SerializeField] private float grabHeight = 2.5f;

    [Header("Sensor configuration")]
    [SerializeField] private Material sensorMaterial;

    //Model values
    private readonly Transform orientation; // this will probably go unused unless we implement animations or models

    // Sensor values
    private GameObject sensorsContainer; // Wrapper for the colliders
    private GameObject contactSensor;
    private Dictionary<char, SensorTrigger> sensors;
    public static bool showColliders = false;

    // Enviroment
    private Vector3 targetPosition;
    private Coroutine moveCorutine;
    private Coroutine grabObjCorutine;


    private void Awake()
    {

        SetupCollisionMatrix();
        GenerateSensors();
    }


    void Update()
    {
        UpdateSensorPositions();
        UpdateContactSensorPosition();
        UpdateColliderVisibility();
    }

    // Utils
    public static readonly char[] directionNames = { 'F', 'B', 'L', 'R' };

    private Vector2Int Name2Direction(char name)
    {
        switch (name)
        {
            case 'F':
                return Vector2Int.up;
            case 'B':
                return Vector2Int.down;
            case 'L':
                return Vector2Int.left;
            case 'R':
                return Vector2Int.right;
            default:
                Debug.LogError($"Invalid direction name: {name}.");
                return pos;
        }
    }

    public async Task ExecuteAction(string action)
    {
        actionCompletionSource = new TaskCompletionSource<bool>();

        switch (action[0])
        {
            case 'M':
                await Move(action[1], EnvironmentManager.iterationDuration);
                break;
            case 'G':
                await Grab(action[1], EnvironmentManager.iterationDuration);
                break;
            case 'D':
                await Drop(action[1], EnvironmentManager.iterationDuration);
                break;
            default:
                Debug.LogError($"Unknown action: {action}");
                actionCompletionSource.SetResult(true);
                break;
        }

        await actionCompletionSource.Task;
    }

    public void ActionCompleted()
    {
        actionCompletionSource?.TrySetResult(true);
    }

    // Updaters
    public async Task Move(char direction, float timeToMove)
    {
        // Check for initial collision
        int value = IsColliding(direction);
        Vector2Int newPos = pos + Name2Direction(direction);
        if (value != 0)
        {
            Debug.LogWarning($"Ag:{id} tried to move into an {Utils.Col2Type(value)}!");
            return;
        }

        hasCollided = false;
        pos = newPos;

        // Calculate the new target position
        targetPosition = Enviroment.CalculateObjectPosition(pos);

        Vector3 startPos = transform.position;
        float elapsedTime = 0f;
        while (elapsedTime < EnvironmentManager.iterationDuration)
        {
            elapsedTime += Time.deltaTime;
            float t = Mathf.Clamp01(elapsedTime / timeToMove);
            transform.position = Vector3.Lerp(startPos, targetPosition, t);
            if (hasCollided)
            {
                float remainingTime = timeToMove - elapsedTime;
                await Move(Utils.OppositeDir(direction), remainingTime);
                return;
            }
            await Task.Yield();
        }
        transform.position = targetPosition;
    }

    public async Task Grab(char dir, float timeToMove)
    {
        if (hasObject)
        {
            Debug.LogWarning($"Ag:{id} Already holding an object");
            return;
        }

        Collider directionCollider = sensors[dir].transform.GetComponent<Collider>();
        Object objectToGrab = FindObjectInCollider(directionCollider);

        if (objectToGrab == null)
        {
            Debug.LogError($"Ag:{id} No object to grab in direction {dir}");
            return;
        }

        if (!await objectToGrab.TryGrab())
        {
            Debug.LogWarning($"Ag:{id} Failed to grab object, it was already being grabbed");
            return;
        }

        Vector3 objStartPos = objectToGrab.transform.position;
        Vector3 agStartPos = transform.position;
        Vector2Int newPos = pos + Name2Direction(dir);
        Vector3 targetPosition = Enviroment.CalculateObjectPosition(newPos);
        Vector3 aboveAgentPos = targetPosition + Vector3.up * grabHeight;

        float elapsedTime = 0f;
        bool grabSuccessful = true;

        try
        {
            while (elapsedTime < EnvironmentManager.iterationDuration)
            {
                float remainingTime = EnvironmentManager.iterationDuration - elapsedTime;
                float t = Mathf.Clamp01(elapsedTime / timeToMove);

                objectToGrab.transform.position = Vector3.Lerp(objStartPos, aboveAgentPos, t);
                transform.position = Vector3.Lerp(agStartPos, targetPosition, t);

                if (!objectToGrab.gameObject.activeSelf)
                {
                    grabSuccessful = false;
                    break;
                }

                elapsedTime += Time.deltaTime;
                await Task.Yield();

                if (elapsedTime >= timeToMove)
                    break;
            }

            if (grabSuccessful)
            {
                objectToGrab.transform.position = aboveAgentPos;
                transform.position = targetPosition;
                hasObject = true;
                grabbedObject = objectToGrab;
                objectToGrab.ObjGrab(transform);
                pos = newPos;
            }
            else
            {
                float remainingTime = Mathf.Max(0, EnvironmentManager.iterationDuration - elapsedTime);
                await MoveBack(agStartPos, remainingTime);
                Debug.LogWarning($"Ag:{id} Failed to grab object, it was deactivated during grab attempt");
            }
        }
        finally
        {
            if (!grabSuccessful)
            {
                objectToGrab.CancelGrab();
            }
        }
    }

    private async Task MoveBack(Vector3 startPos, float duration)
    {
        float elapsedTime = 0f;
        Vector3 currentPos = transform.position;

        while (elapsedTime < duration)
        {
            float t = elapsedTime / duration;
            transform.position = Vector3.Lerp(currentPos, startPos, t);
            elapsedTime += Time.deltaTime;
            await Task.Yield();
        }

        transform.position = startPos;
    }

    public async Task Drop(char dir, float timeToMove)
    {
        Debug.Log($"Ag:{id} trying to drop item {dir}");
        if (!hasObject || grabbedObject == null)
        {
            Debug.LogWarning($"Ag:{id} No object to drop");
            return;
        }

        Collider directionCollider = sensors[dir].transform.GetComponent<Collider>();
        Stack targetStack = FindStackInCollider(directionCollider);
        if (targetStack == null)
        {
            Debug.LogError($"Ag:{id} No stack to drop into in direction {dir}");
            return;
        }

        if (!targetStack.TryLockForDropAsync())
        {
            Debug.LogWarning($"Ag:{id} Stack is currently being used by another agent");
            return;
        }

        Vector3 objStartPos = grabbedObject.transform.position;
        Vector3 targetPos = targetStack.GetNextItemPosition(targetStack.nItems + 1);
        float elapsedTime = 0f;
        bool dropSuccessful = false;

        try
        {
            grabbedObject.isMoving = true;
            while (elapsedTime < timeToMove)
            {
                float t = elapsedTime / timeToMove;
                grabbedObject.transform.position = Vector3.Lerp(objStartPos, targetPos, t);
                elapsedTime += Time.deltaTime;
                await Task.Yield();
            }

            // Ensure the object is at the final position
            grabbedObject.transform.position = targetPos;

            dropSuccessful = targetStack.TryAddItemAsync(grabbedObject);

            if (dropSuccessful)
            {
                hasObject = false;
                grabbedObject.ObjDrop(targetStack);
                grabbedObject = null;
            }
            else
            {
                grabbedObject.isMoving = false;
                Debug.LogWarning($"Ag:{id} Failed to drop object into the stack!");
                await MoveObjectBack(objStartPos, Mathf.Max(0, EnvironmentManager.iterationDuration - timeToMove));
            }
        }
        catch (System.Exception e)
        {
            Debug.LogError($"Ag:{id} Error during drop: {e.Message}");
            await MoveObjectBack(objStartPos, Mathf.Max(0, EnvironmentManager.iterationDuration - elapsedTime));
        }
        finally
        {
            targetStack.UnlockForDrop();
        }
    }


    private async Task MoveObjectBack(Vector3 startPos, float duration)
    {
        float elapsedTime = 0f;
        Vector3 currentPos = grabbedObject.transform.position;

        while (elapsedTime < duration)
        {
            float t = elapsedTime / duration;
            grabbedObject.transform.position = Vector3.Lerp(currentPos, startPos, t);
            elapsedTime += Time.deltaTime;
            await Task.Yield();
        }

        grabbedObject.transform.position = startPos;
    }


    private Object FindObjectInCollider(Collider directionCollider)
    {
        Collider[] colliders = Physics.OverlapBox(directionCollider.bounds.center, directionCollider.bounds.extents, directionCollider.transform.rotation, LayerMask.GetMask("Objects"));

        foreach (Collider collider in colliders)
        {
            Object obj = collider.GetComponent<Object>();
            if (obj != null)
            {
                return obj;
            }
        }

        return null;
    }

    private Stack FindStackInCollider(Collider directionCollider)
    {
        Collider[] colliders = Physics.OverlapBox(directionCollider.bounds.center, directionCollider.bounds.extents, directionCollider.transform.rotation, LayerMask.GetMask("Stacks"));

        foreach (Collider collider in colliders)
        {
            if (collider.TryGetComponent<Stack>(out var stck))
            {
                return stck;
            }
        }

        return null;
    }

    private int IsColliding(char direction)
    {
        int value = cols[direction];

        if (value != 0)
            return value;
        else
            return 0;
    }

    public void UpdateSensorValue(char direction, int value)
    {
        cols[direction] = value;
    }

    private void UpdateSensorPositions()
    {
        foreach (KeyValuePair<char, SensorTrigger> sensor in sensors)
        {
            SensorTrigger trigger = sensor.Value;
            trigger.transform.position = transform.position;
        }
    }

    public Task<Dictionary<char, int>> GetSensorData()
    {
        Dictionary<char, int> newCols = new Dictionary<char, int>();
        foreach (KeyValuePair<char, SensorTrigger> sensor in sensors)
        {
            char direction = sensor.Key;
            SensorTrigger trigger = sensor.Value;
            newCols[direction] = trigger.GetSensorValue();
        }

        return Task.FromResult(newCols);
    }

    private void UpdateContactSensorPosition()
    {
        contactSensor.transform.position = transform.position + new Vector3(0f, 1.5f, 0f);
    }

    private void UpdateColliderVisibility()
    {
        foreach (KeyValuePair<char, SensorTrigger> sensor in sensors)
        {
            SensorTrigger sensorTrigger = sensor.Value;
            sensorTrigger.transform.GetChild(0).gameObject.SetActive(showColliders);
        }
    }

    public static void ToggleColliderVisibility()
    {
        showColliders = !showColliders;
    }

    // Sensor Setup
    // This setups to what the colliders will be able to collide with
    private void SetupCollisionMatrix()
    {
        // Sensors only interact with Agents, Objects, and Obstacles
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensors"), LayerMask.NameToLayer("Sensors"), true);
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensors"), LayerMask.NameToLayer("Tiles"), true);
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensors"), LayerMask.NameToLayer("Contact"), true);
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensors"), LayerMask.NameToLayer("Obstacles"), false);
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensors"), LayerMask.NameToLayer("Stacks"), false);
    }

    private void GenerateSensors()
    {
        // Create the sensors container
        sensorsContainer = new GameObject("SensorsContainer");
        sensorsContainer.transform.SetParent(transform);
        sensorsContainer.transform.localPosition = Vector3.zero;

        sensors = new Dictionary<char, SensorTrigger>();

        sensors['F'] = GenerateSensor("Sens:F", Utils.directions[0]);
        sensors['B'] = GenerateSensor("Sens:B", Utils.directions[1]);
        sensors['L'] = GenerateSensor("Sens:L", Utils.directions[2]);
        sensors['R'] = GenerateSensor("Sens:R", Utils.directions[3]);

        foreach (KeyValuePair<char, SensorTrigger> sensor in sensors)
        {
            SensorTrigger trigger = sensor.Value;
            trigger.transform.parent = sensorsContainer.transform;
        }

        Utils.SetLayerRecursivelyByName(sensorsContainer, "Sensors");

        GameObject contactSensorWrapper = new GameObject("ContactSensor");
        contactSensor = GenerateContactSensor("ConSensor");
        contactSensor.transform.parent = contactSensorWrapper.transform;

        Utils.SetLayerRecursivelyByName(contactSensorWrapper, "Contact");
    }

    private SensorTrigger GenerateSensor(string name, Vector2Int direction)
    {
        GameObject sensor = new GameObject(name);
        sensor.transform.SetParent(transform); // Set the subject of this script as the parent
        sensor.layer = LayerMask.NameToLayer("Sensors");


        SphereCollider collider = sensor.AddComponent<SphereCollider>();
        collider.isTrigger = true;
        collider.radius = (Enviroment.tileSize / 2) - 0.2f;
        collider.center = FlatDir23DDir(direction) * (Enviroment.tileSize - 1f) + new Vector3(0, 0.5f, 0);

        SensorTrigger trigger = collider.AddComponent<SensorTrigger>();
        trigger.parentAgent = this;
        trigger.direction = Utils.Direction2Name(direction);

        // Crate visualizer
        GameObject visualizer = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        visualizer.transform.SetParent(sensor.transform);
        visualizer.transform.localPosition = collider.center;
        visualizer.transform.localScale = Vector3.one * (collider.radius * 2);
        Destroy(visualizer.GetComponent<SphereCollider>()); // Remove colliders since they are not needed
        visualizer.transform.GetComponent<Renderer>().material = sensorMaterial;
        visualizer.SetActive(showColliders);

        return trigger;
    }

    private GameObject GenerateContactSensor(string name)
    {
        GameObject sensor = new GameObject(name);
        sensor.transform.SetParent(transform);
        sensor.layer = LayerMask.NameToLayer("Obstacles");

        BoxCollider collider = sensor.AddComponent<BoxCollider>();
        collider.isTrigger = true;
        collider.size = new Vector3(0.8f, 0.8f, 0.8f);
        collider.center = Vector3.zero;
        collider.transform.rotation = Quaternion.Euler(0, 45, 0);

        ContactTrigger trigger = collider.AddComponent<ContactTrigger>();
        trigger.parentAgent = this;

        return sensor;
    }

    private Vector3 FlatDir23DDir(Vector2Int direction)
    {
        if (direction == Vector2Int.up) return Vector3.forward;
        if (direction == Vector2Int.down) return Vector3.back;
        if (direction == Vector2Int.left) return Vector3.left;
        if (direction == Vector2Int.right) return Vector3.right;
        return Vector3.zero; // Default case, should not happen with your current Utils.directions array
    }

}

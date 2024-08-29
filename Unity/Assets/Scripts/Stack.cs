using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Threading;
using System.Threading.Tasks;

public class Stack : MonoBehaviour
{
    [Header("Stack values")]
    [SerializeField] private float verticalItemOffset = 2f; // Adjust this value as needed
    public int id;
    public Vector2Int pos;
    public int nItems = 0;
    public int maxItems = 5;  // Set this to your desired maximum stack size 
    public bool IsFull => nItems >= maxItems;
    public static event System.Action<Stack> OnStackFull;

    [Header("Engine values")]
    public Enviroment parentEnv;
    
    private float itemScale = 0.8f; // Adjust this value as needed
    private bool isLocked = false;
    private List<Object> items;


    private void Awake()
    {
        transform.localScale = new Vector3(Enviroment.tileSize - 1f, Enviroment.tileSize/3*2, Enviroment.tileSize - 1f);
        transform.position += new Vector3(0f,Enviroment.tileSize/2,0f);
        transform.gameObject.layer = LayerMask.NameToLayer("Stacks");
        items = new List<Object>();
    }

    public Vector3 GetNextItemPosition(int nItems)
    {
        if(nItems == 1)
        {
            return transform.position;
        }
        return transform.position + Vector3.up * ((nItems - 1) * verticalItemOffset);
    }

    public bool TryLockForDropAsync()
    {
        if (isLocked || nItems >= maxItems)
            return false;

        isLocked = true;
        return true;
    }

    public void UnlockForDrop()
    {
        isLocked = false;
    }


    public bool TryAddItemAsync(Object item)
    {
        if (nItems >= maxItems)
            return false;

        items.Add(item);
        nItems++;

        // Scale down the item
        item.transform.localScale *= itemScale;

        // Position the item
        item.transform.position = GetNextItemPosition(nItems);

        item.GetComponent<Collider>().enabled = false;

        // Disable item's collider
        Collider itemCollider = item.GetComponent<Collider>();
        if (itemCollider != null)
            itemCollider.enabled = false;

        // Check if stack is full after adding item
        if (IsFull)
        {
            gameObject.layer = LayerMask.NameToLayer("Obstacles");
            OnStackFull?.Invoke(this);
        }

        return true;
    }
}